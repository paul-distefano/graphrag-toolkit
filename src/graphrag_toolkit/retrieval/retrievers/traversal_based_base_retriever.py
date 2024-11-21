# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import abc
import time
from typing import List, Any, Type, Optional

from graphrag_toolkit.storage.graph_store import GraphStore
from graphrag_toolkit.storage.vector_store import VectorStore
from graphrag_toolkit.retrieval.model import SearchResultCollection, SearchResult, Source, ScoredEntity
from graphrag_toolkit.retrieval.processors import *

from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode

logger = logging.getLogger(__name__)

DEFAULT_PROCESSORS = [
    DedupResults,
    DisaggregateResults,                
    PopulateStatementStrs,
    RerankStatements,
    RescoreResults,
    SortResults,
    TruncateResults,
    TruncateStatements,
    ClearChunks,
    StatementsToStrings,
    SimplifySingleTopicResults
]

class TraversalBasedBaseRetriever(BaseRetriever):

    def __init__(self, 
                 graph_store:GraphStore,
                 vector_store:VectorStore,
                 processor_args:Optional[ProcessorArgs]=None,
                 processors:Optional[List[Type[ProcessorBase]]]=None,
                 entities:Optional[List[ScoredEntity]]=None,
                 **kwargs):
        
        self.args = processor_args or ProcessorArgs(**kwargs)
        
        self.graph_store = graph_store
        self.vector_store = vector_store
        self.processors = processors if processors is not None else DEFAULT_PROCESSORS
        self.entities = entities or []
        
    def create_cypher_query(self, match_clause):

        return_clause = f'''
        WITH DISTINCT l, t LIMIT $statementLimit
        MATCH (l:Statement)-[:MENTIONED_IN]->(c:Chunk)-[:EXTRACTED_FROM]->(s:Source)
        OPTIONAL MATCH (f:Fact)-[:SUPPORTS]->(l:Statement)
        WITH {{ sourceId: {self.graph_store.node_id("s.sourceId")}, metadata: s{{.*}}}} AS source,
            t,
            {{ chunkId: {self.graph_store.node_id("c.chunkId")}, value: NULL }} AS cc, 
            {{ statement: l.value, facts: collect(distinct f.value), details: l.details, chunkId: {self.graph_store.node_id("c.chunkId")}, score: count(l) }} as ll
        WITH source, 
            t, 
            collect(distinct cc) as chunks, 
            collect(distinct ll) as statements
        WITH source,
            {{ 
                topic: t.value, 
                chunks: chunks,
                statements: statements
            }} as topic
        RETURN {{
            score: sum(size(topic.statements)/size(topic.chunks)), 
            source: source,
            topics: collect(distinct topic)
        }} as result ORDER BY result.score DESC LIMIT $limit'''

        return f'{match_clause}{return_clause}'

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:

        logger.debug(f'[{type(self).__name__}] Begin retrieve [args: {self.args.to_dict()}]')

        def source_to_dict(source:Source):
            source_dict = source.model_dump()
            source_dict['metadata'] = { k:v for k,v in source_dict['metadata'] }
            return source_dict
        
        start_retrieve = time.time()
        
        start_node_ids = self.get_start_node_ids(query_bundle)
        search_results:SearchResultCollection = self.do_graph_search(query_bundle, start_node_ids)

        end_retrieve = time.time()

        for processor in self.processors:
            search_results = processor(self.args).process_results(search_results, query_bundle, type(self).__name__)

        end_processing = time.time()
            
        sources = [source_to_dict(search_result.source) for search_result in search_results.results]
        
        if self.args.strip_source_metadata:
            for search_result in search_results.results:
                search_result.source.metadata = []

        retrieval_ms = (end_retrieve-start_retrieve) * 1000
        processing_ms = (end_processing-end_retrieve) * 1000

        logger.debug(f'[{type(self).__name__}] Retrieval: {retrieval_ms:.2f}ms')
        logger.debug(f'[{type(self).__name__}] Processing: {processing_ms:.2f}ms')

        return [
            NodeWithScore(
                node=TextNode(
                    text=search_result.model_dump_json(exclude_none=True, exclude_defaults=True, indent=2),
                    metadata={
                        'source': source
                    }
                ), 
                score=search_result.score
            ) 
            for (search_result, source) in zip(search_results.results, sources)
        ]
    
    def _to_search_results_collection(self, results:List[Any]) -> SearchResultCollection:

        def to_metadata_list(metadata):
            return [(k, v) for k, v in metadata.items()]

        for result in results:
            result['result']['source']['metadata'] = to_metadata_list(result['result']['source']['metadata'])
        
        search_results = [
            SearchResult.model_validate(result['result']) 
            for result in results
        ]

        return SearchResultCollection(results=search_results)

    @abc.abstractmethod
    def get_start_node_ids(self, query_bundle: QueryBundle) -> List[str]:
        pass
    
    @abc.abstractmethod
    def do_graph_search(self, query_bundle: QueryBundle, start_node_ids:List[str]) -> SearchResultCollection:
        pass