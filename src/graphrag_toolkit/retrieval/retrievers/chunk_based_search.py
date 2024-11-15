# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import queue
import concurrent.futures
from typing import List, Optional, Type

from graphrag_toolkit.retrieval.model import SearchResultCollection
from graphrag_toolkit.storage.vector_store import VectorStore
from graphrag_toolkit.storage.graph_store import GraphStore
from graphrag_toolkit.retrieval.processors import ProcessorBase, ProcessorArgs
from graphrag_toolkit.retrieval.retrievers.traversal_based_base_retriever import TraversalBasedBaseRetriever

from llama_index.core.schema import QueryBundle

logger = logging.getLogger(__name__)

class ChunkBasedSearch(TraversalBasedBaseRetriever):
    def __init__(self, 
                 graph_store:GraphStore,
                 vector_store:VectorStore,
                 processor_args:Optional[ProcessorArgs]=None,
                 processors:Optional[List[Type[ProcessorBase]]]=None,
                 **kwargs):
        
        super().__init__(
            graph_store=graph_store, 
            vector_store=vector_store,
            processor_args=processor_args,
            processors=processors,
            **kwargs
        )

    def _get_diverse_chunks(self, query_bundle: QueryBundle):
        
        query = query_bundle.query_str
        num_chunks = self.args.vss_top_k * self.args.vss_diversity_factor
        
        chunks = self.vector_store.get_index('chunk').top_k(query, top_k=num_chunks)
        
        source_map = {}
        
        for chunk in chunks:
            source_id = chunk['source']['sourceId']
            if source_id not in source_map:
                source_map[source_id] = queue.Queue()
            source_map[source_id].put(chunk)
            
        chunks_by_source = queue.Queue()
        
        for source_chunks in source_map.values():
            chunks_by_source.put(source_chunks)
        
        diverse_chunks = []
        
        while (not chunks_by_source.empty()) and len(diverse_chunks) < self.args.vss_top_k:
            source_chunks = chunks_by_source.get()
            diverse_chunks.append(source_chunks.get())
            if not source_chunks.empty():
                chunks_by_source.put(source_chunks)

        logger.debug('Diverse chunks:\n' + '\n--------------\n'.join([str(chunk) for chunk in diverse_chunks]))

        return diverse_chunks
    
    def chunk_based_graph_search(self, chunk_id):

        cypher = self.create_cypher_query(f'''
        // chunk-based graph search                                  
        MATCH (l:Statement)-[:PREVIOUS*0..1]-(:Statement)-[:BELONGS_TO]->(t:Topic)-[:MENTIONED_IN]->(c:Chunk)
        WHERE {self.graph_store.node_id("c.chunkId")} = $chunkId
        ''')
                                          
        properties = {
            'chunkId': chunk_id,
            'limit': self.args.query_limit,
            'statementLimit': self.args.intermediate_limit
        }
                                          
        return self.graph_store.execute_query(cypher, properties)


    def get_start_node_ids(self, query_bundle: QueryBundle) -> List[str]:

        logger.debug('Getting start node ids for chunk-based search...')

        chunks = self._get_diverse_chunks(query_bundle)
        
        return [chunk['chunk']['chunkId'] for chunk in chunks]
    
    def do_graph_search(self, query_bundle: QueryBundle, start_node_ids:List[str]) -> SearchResultCollection:
        
        chunk_ids = start_node_ids

        logger.debug('Running chunk-based search...')
        
        search_results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.args.num_workers) as executor:

            futures = [
                executor.submit(self.chunk_based_graph_search, chunk_id)
                for chunk_id in chunk_ids
            ]
            
            executor.shutdown()

            for future in futures:
                for result in future.result():
                    search_results.append(result)
                    
        search_results_collection = self._to_search_results_collection(search_results) 
        
        retriever_name = type(self).__name__
        if retriever_name in self.args.debug_results and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'''Chunk-based results: {search_results_collection.model_dump_json(
                    indent=2, 
                    exclude_unset=True, 
                    exclude_defaults=True, 
                    exclude_none=True, 
                    warnings=False)
                }''')
                   
        
        return search_results_collection
    
