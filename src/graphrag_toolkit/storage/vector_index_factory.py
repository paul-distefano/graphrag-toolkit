# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging

from graphrag_toolkit.storage.opensearch_vector_indexes import OpenSearchIndex
from graphrag_toolkit.storage.neptune_vector_indexes import NeptuneIndex
from graphrag_toolkit.storage.vector_index import DummyVectorIndex

logger = logging.getLogger(__name__)

OPENSEARCH_SERVERLESS = 'aoss://'
NEPTUNE_ANALYTICS = 'neptune-graph://'
DUMMY_VECTOR_STORE = 'vector://'

def vector_info_resolver(vector_index_info:str=None):

    OPENSEARCH_SERVERLESS_DNS = 'aoss.amazonaws.com'

    if not vector_index_info or vector_index_info.startswith(DUMMY_VECTOR_STORE):
        return (DUMMY_VECTOR_STORE, None)
    if vector_index_info.startswith(OPENSEARCH_SERVERLESS):
        return (OPENSEARCH_SERVERLESS, vector_index_info[len(OPENSEARCH_SERVERLESS):])
    elif vector_index_info.startswith(NEPTUNE_ANALYTICS):
        return (NEPTUNE_ANALYTICS, vector_index_info[len(NEPTUNE_ANALYTICS):]) 
    elif vector_index_info.endswith(OPENSEARCH_SERVERLESS_DNS):
        return (OPENSEARCH_SERVERLESS, vector_index_info)
    else:
        return (NEPTUNE_ANALYTICS, vector_index_info) 
    
class VectorIndexFactory():

    @staticmethod
    def for_vector_index(index_name, vector_index_info:str=None, **kwargs):

        (vector_index_type, init_info) = vector_info_resolver(vector_index_info)

        if vector_index_type == OPENSEARCH_SERVERLESS:
            logger.debug(f"Opening OpenSearch vector index [index_name: {index_name}, endpoint: {init_info}]")
            return VectorIndexFactory.for_opensearch(index_name, init_info, **kwargs)
        elif vector_index_type == NEPTUNE_ANALYTICS:
            logger.debug(f"Opening Neptune Analytics vector index [index_name: {index_name}, graph_id: {init_info}]")
            return VectorIndexFactory.for_neptune_analytics(index_name, init_info, **kwargs)
        else:
            logger.debug(f"Opening dummy vector store [index_name: {index_name}]")
            return VectorIndexFactory.for_dummy_vector_index(index_name, **kwargs)
    
    @staticmethod
    def for_opensearch(index_name, endpoint, **kwargs):
        return OpenSearchIndex.for_index(index_name, endpoint, **kwargs)

    @staticmethod
    def for_neptune_analytics(index_name, graph_id, **kwargs):
        return NeptuneIndex.for_index(index_name, graph_id, **kwargs)
        
    @staticmethod
    def for_dummy_vector_index(index_name, *args, **kwargs):
        return DummyVectorIndex(index_name=index_name)