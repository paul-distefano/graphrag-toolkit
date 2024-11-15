# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import boto3
import json
import logging
import aiohttp
import asyncio
from typing import List

from llama_index.core.bridge.pydantic import PrivateAttr
from llama_index.core.schema import BaseNode, NodeWithScore, QueryBundle
from llama_index.core.async_utils import asyncio_run
from llama_index.vector_stores.opensearch import OpensearchVectorClient
from llama_index.core.vector_stores.types import  VectorStoreQueryResult, VectorStoreQueryMode
from llama_index.core.embeddings.utils import EmbedType
from llama_index.core.indices.utils import embed_nodes

from opensearchpy.exceptions import NotFoundError
from opensearchpy import AWSV4SignerAsyncAuth, AsyncHttpConnection, AWSV4SignerAuth
from opensearchpy.exceptions import NotFoundError

from graphrag_toolkit.config import GraphRAGConfig
from graphrag_toolkit.storage.vector_index import VectorIndex, to_embedded_query
from graphrag_toolkit.storage.constants import INDEX_KEY, EMBEDDING_INDEXES

logger = logging.getLogger(__name__)
    
def try_close_session():
    try:
        client_session = aiohttp.ClientSession()
        if client_session:
            asyncio_run(client_session.close())
    except Exception as err:
        logger.warning(f'Error while trying to close session [error: {err}]')

    
def create_opensearch_vector_client(endpoint, index_name, dimensions, embed_model):
    
    session = boto3.Session()
    region = session.region_name
    credentials = session.get_credentials()
    service = 'aoss'
        
    auth = AWSV4SignerAsyncAuth(credentials, region, service)
        
    text_field = 'value'
    embedding_field = 'embedding'

    logger.debug(f'Creating OpenSearch vector client [endpoint: {endpoint}, index_name={index_name}, embed_model={embed_model}, dimensions={dimensions}]')
 
    client = None
    retry_count = 0
    while not client:
        try:
            client = OpensearchVectorClient(
                endpoint, 
                index_name, 
                dimensions, 
                embedding_field=embedding_field, 
                text_field=text_field,  
                use_ssl=True, 
                verify_certs=True,
                http_auth=auth,
                connection_class=AsyncHttpConnection,
                timeout=300,
                max_retries=10,
                retry_on_timeout=True,
            )
        except NotFoundError as err:
            retry_count += 1
            logger.warning(f'Error while creating OpenSearch vector client [retry_count: {retry_count}, error: {err}]')
            try_close_session()
            if retry_count > 3:
                raise err
                
    logger.debug(f'Created OpenSearch vector client [client: {client}, retry_count: {retry_count}]')
            
    return client
    
class OpenSearchIndex(VectorIndex):

    @staticmethod
    def for_index(index_name, endpoint, embed_model=None, dimensions=None):
        embed_model = embed_model or GraphRAGConfig.embed_model
        dimensions = dimensions or GraphRAGConfig.embed_dimensions

        # create and close client to ensure index is created
        client = create_opensearch_vector_client(
            endpoint, 
            index_name, 
            dimensions, 
            embed_model
        )
        asyncio_run(client._os_client.close())
        return OpenSearchIndex(index_name=index_name, endpoint=endpoint, dimensions=dimensions, embed_model=embed_model)
    
    class Config:
        arbitrary_types_allowed = True

    endpoint: str
    index_name: str
    dimensions:int
    embed_model:EmbedType

    _client: OpensearchVectorClient = PrivateAttr(default=None)
        
    @property
    def client(self) -> OpensearchVectorClient:
        if not self._client:
            self._client = create_opensearch_vector_client(
                self.endpoint, 
                self.index_name, 
                self.dimensions, 
                self.embed_model
            )
        return self._client

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        try_close_session()           
              
    def _clean_id(self, s):
        return ''.join(c for c in s if c.isalnum())
    
    def _to_top_k_result(self, r):
        
        result = {
            'score': r.score 
        }
    
        for k,v in r.metadata.items():
            if k != INDEX_KEY:
                result[k] = v
            
        return result
        
    def _to_get_embedding_result(self, hit):
        
        source = hit['_source']
        data = json.loads(source['metadata']['_node_content'])

        result = {
            'id': source['id'],
            'value': source['value'],
            'embedding': source['embedding']
        }

        for k,v in data['metadata'].items():
            if k != INDEX_KEY:
                result[k] = v
            
        return result
    
    def _add_metadata(self, source, target, key):
        i = source.get(key, None)
        if i:
            target[key] = i
        return target

    def add_embeddings(self, nodes):
        
        id_to_embed_map = embed_nodes(
            nodes, self.embed_model
        )
        
        docs = []
        
        for node in nodes:

            index_metadata = node.metadata[INDEX_KEY]
            
            doc:BaseNode = node.copy()
            
            metadata = {
                INDEX_KEY: index_metadata
            }
            
            metadata = self._add_metadata(node.metadata, metadata, 'source')  
            
            for i in EMBEDDING_INDEXES:
                metadata = self._add_metadata(node.metadata, metadata, i)  

            doc.metadata = metadata

            doc.embedding = id_to_embed_map[node.node_id]
                
            docs.append(doc)
        
        if docs:
            asyncio.get_event_loop().run_until_complete(
                self.client.index_results(docs)
            )
        
        return nodes
    
    def top_k(self, query:str, top_k:int=5):

        query_bundle:QueryBundle = to_embedded_query(query, self.embed_model)
        
        results:VectorStoreQueryResult = asyncio.get_event_loop().run_until_complete(
            self.client.aquery(
                VectorStoreQueryMode.DEFAULT, 
                query_str=query_bundle.query_str, 
                query_embedding=query_bundle.embedding, 
                k=top_k
            )
        )

        scored_nodes = [
            NodeWithScore(node=node, score=score) 
            for node, score in zip(results.nodes, results.similarities)
        ]

        return [self._to_top_k_result(node) for node in scored_nodes]

    # opensearch has a limit of 10,000 results per search, so we use this to paginate the search
    async def paginated_search(self, query, page_size=10000, max_pages=None):
        client = self.client._os_client
        search_after = None
        page = 0
        
        while True:
            body = {
                "size": page_size,
                "query": query,
                "sort": [{"_id": "asc"}]
            }
            
            if search_after:
                body["search_after"] = search_after

            response = await client.search(
                index=self.index_name,
                body=body
            )

            hits = response['hits']['hits']
            if not hits:
                break

            yield hits

            search_after = hits[-1]['sort']
            page += 1

            if max_pages and page >= max_pages:
                break

    async def get_all_embeddings(self, query:str, max_results=None):
        all_results = []
        async for page in self.paginated_search(query, page_size=10000):
            all_results.extend(self._to_get_embedding_result(hit) for hit in page)
            if max_results and len(all_results) >= max_results:
                all_results = all_results[:max_results]
                break
        return all_results
    
    def get_embeddings(self, ids:List[str]=[]):
        query = {
            "terms": {
                f'metadata.{INDEX_KEY}.key': [self._clean_id(i) for i in ids]
            }
        }
        
        return asyncio.get_event_loop().run_until_complete(
            self.get_all_embeddings(query, max_results=len(ids) * 2)
        )
