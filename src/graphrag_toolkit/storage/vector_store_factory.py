# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Union
from graphrag_toolkit.storage import VectorStore, VectorIndexFactory
from graphrag_toolkit.storage.constants import EMBEDDING_INDEXES

VectorStoreType = Union[str, VectorStore]

class VectorStoreFactory():

    @staticmethod
    def for_vector_store(vector_store_info:str=None, index_names=EMBEDDING_INDEXES, **kwargs):
        if vector_store_info and isinstance(vector_store_info, VectorStore):
            return vector_store_info
        return VectorStore([VectorIndexFactory.for_vector_index(index_name, vector_store_info, **kwargs) for index_name in index_names])
    
    @staticmethod
    def for_opensearch(endpoint, embed_model=None, index_names=EMBEDDING_INDEXES, vector_existence_check=None, **kwargs):
        return VectorStore([VectorIndexFactory.for_opensearch(index_name, endpoint, embed_model=embed_model, vector_existence_check=vector_existence_check, **kwargs) for index_name in index_names])

    @staticmethod
    def for_neptune_analytics(graph_id, embed_model=None, index_names=EMBEDDING_INDEXES, **kwargs):
        return VectorStore([VectorIndexFactory.for_neptune_analytics(index_name, graph_id, embed_model=embed_model, **kwargs) for index_name in index_names])
        
    @staticmethod
    def for_dummy_vector_index(index_names=EMBEDDING_INDEXES):
        return VectorStore([VectorIndexFactory.for_dummy_vector_index(index_name) for index_name in index_names])
    
    @staticmethod
    def for_composite(vector_store_list:List[VectorStore]):
        indexes = []
        for v in vector_store_list:
            indexes.extend(v.indexes.values())            
        return VectorStore(indexes)