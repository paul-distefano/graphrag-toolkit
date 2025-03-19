# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import List, Optional, Type, Union

from graphrag_toolkit.retrieval.model import SearchResultCollection, ScoredEntity, Entity, SearchResult
from graphrag_toolkit.storage.graph_store import GraphStore
from graphrag_toolkit.storage.vector_store import VectorStore
from graphrag_toolkit.retrieval.retrievers.keyword_entity_search import KeywordEntitySearch
from graphrag_toolkit.retrieval.retrievers.chunk_based_search import ChunkBasedSearch
from graphrag_toolkit.retrieval.retrievers.topic_based_search import TopicBasedSearch
from graphrag_toolkit.retrieval.processors import ProcessorBase, ProcessorArgs
from graphrag_toolkit.retrieval.retrievers.traversal_based_base_retriever import TraversalBasedBaseRetriever

from llama_index.core.schema import QueryBundle

logger = logging.getLogger(__name__)

SubRetrieverType = Union[ChunkBasedSearch, TopicBasedSearch, Type[ChunkBasedSearch], Type[TopicBasedSearch]]

class EntityContextSearch(TraversalBasedBaseRetriever):
    def __init__(self, 
                 graph_store:GraphStore,
                 vector_store:VectorStore,
                 processor_args:Optional[ProcessorArgs]=None,
                 processors:Optional[List[Type[ProcessorBase]]]=None,
                 sub_retriever:Optional[SubRetrieverType]=None,
                 **kwargs):
        
        self.sub_retriever = sub_retriever or ChunkBasedSearch
        
        super().__init__(
            graph_store=graph_store, 
            vector_store=vector_store,
            processor_args=processor_args,
            processors=processors,
            **kwargs
        )

    def get_start_node_ids(self, query_bundle: QueryBundle) -> List[str]:

        logger.debug('Getting start node ids for entity context search...')
        
        keyword_entity_search = KeywordEntitySearch(
            graph_store=self.graph_store, 
            max_keywords=self.args.max_keywords,
            expand_entities=False
        )

        entity_search_results = keyword_entity_search.retrieve(query_bundle)

        entities = [
            ScoredEntity(
                entity=Entity.model_validate_json(entity_search_result.text), 
                score=entity_search_result.score
            )
            for entity_search_result in entity_search_results
        ]

        return [entity.entity.entityId for entity in entities]   

    def _get_context_search_strs(self, start_node_ids:List[str]) -> List[str]:

        cypher = f'''
        // get entity context
        MATCH (s:`__Entity__`)-[:`__RELATION__`*1..2]-(c:`__Entity__`)
        WHERE {self.graph_store.node_id("s.entityId")} in $entityIds
        AND NOT {self.graph_store.node_id("c.entityId")} in $entityIds
        RETURN {self.graph_store.node_id("s.entityId")} as s, collect(distinct {self.graph_store.node_id("c.entityId")}) as c
        '''
        
        properties = {
            'entityIds': start_node_ids
        }
        
        results = self.graph_store.execute_query(cypher, properties)
        
        all_entity_ids = set()
        entity_map = {}
        
        for result in results:
            all_entity_ids.add(result['s'])
            all_entity_ids.update(result['c'])
            entity_map[result['s']] = result['c']
            
        cypher = f'''
        // get entity context scores
        MATCH (s:`__Entity__`)-[r:`__RELATION__`]-()
        WHERE {self.graph_store.node_id("s.entityId")} in $entityIds
        RETURN {self.graph_store.node_id("s.entityId")} as s_id, s.value AS value, sum(r.count) AS score
        '''
        
        properties = {
            'entityIds': list(all_entity_ids)
        }
        
        results = self.graph_store.execute_query(cypher, properties)
        
        entity_score_map = {}
        
        for result in results:
            entity_score_map[result['s_id']] = { 'value': result['value'], 'score': result['score']}
            
        context_search_str_map = {}
        
        for s, c in entity_map.items():
            context_search_str = [entity_score_map[s]['value']]
            s_score = entity_score_map[s]['score']
            c_score_total = 0
            for c_item in c:
                c_score = entity_score_map[c_item]['score']
                if c_score <= (self.args.ecs_max_score_factor * s_score) and c_score >= (self.args.ecs_min_score_factor * s_score):
                    context_search_str.append(entity_score_map[c_item]['value'])
                    c_score_total += c_score
            context_search_str = ', '.join(context_search_str[:self.args.ecs_max_context_items])
            if c_score_total > 0:
                context_search_str_map[context_search_str] = (s_score/c_score_total)
        
        logger.debug(f'context_search_str_map: {context_search_str_map}')
        
        context_search_strs = sorted(context_search_str_map, key=context_search_str_map.get, reverse=True)

        return context_search_strs[:self.args.ecs_max_context_search_strs]
    
    def _get_sub_retriever(self):
        sub_retriever = (self.sub_retriever if isinstance(self.sub_retriever, TraversalBasedBaseRetriever) 
                         else self.sub_retriever(
                            self.graph_store, 
                            self.vector_store, 
                            vss_diversity_factor=None,
                            vss_top_k=2,
                            max_search_results=2,
                            include_facts=True
                        ))
        logger.debug(f'sub_retriever: {type(sub_retriever).__name__}')
        return sub_retriever
    
    def do_graph_search(self, query_bundle:QueryBundle, start_node_ids:List[str]) -> SearchResultCollection:

        logger.debug('Running entity-context-based search...')

        sub_retriever = self._get_sub_retriever()
        context_search_strs = self._get_context_search_strs(start_node_ids)

        logger.debug(f'context_search_strs: {context_search_strs}')
        
        search_results = []

        for context_search_str in context_search_strs:
            results = sub_retriever.retrieve(QueryBundle(query_str=context_search_str))
            for result in results:
                search_results.append(SearchResult.model_validate(result.metadata))
                    
                
        search_results_collection = SearchResultCollection(results=search_results) 
        
        retriever_name = type(self).__name__
        
        if retriever_name in self.args.debug_results and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'''Entity context results: {search_results_collection.model_dump_json(
                    indent=2, 
                    exclude_unset=True, 
                    exclude_defaults=True, 
                    exclude_none=True, 
                    warnings=False)
                }''')
        
        return search_results_collection