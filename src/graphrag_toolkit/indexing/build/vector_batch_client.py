# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import List
from graphrag_toolkit.storage import VectorStore
from graphrag_toolkit.storage.vector_index import VectorIndex, DummyVectorIndex
from graphrag_toolkit.storage.constants import EMBEDDING_INDEXES

class BatchVectorIndex():
    def __init__(self, idx:VectorIndex, batch_size:int):
        self.index_name = idx.index_name
        self.index = idx
        self.batch_size = batch_size
        self.nodes = []

    def add_embeddings(self, nodes:List):
        self.nodes.extend(nodes)

    def write_embeddings_to_index(self):

        node_chunks = [
            self.nodes[x:x+self.batch_size] 
            for x in range(0, len(self.nodes), self.batch_size)
        ]
        
        for nodes in node_chunks:
            self.index.add_embeddings(nodes)



class VectorBatchClient():
    def __init__(self, vector_store:VectorStore, batch_writes_enabled:bool, batch_size:int):
        self.indexes = {i.index_name: BatchVectorIndex(i, batch_size) for i in vector_store.indexes.values()}
        self.batch_writes_enabled = batch_writes_enabled

    def get_index(self, index_name):

        if index_name not in EMBEDDING_INDEXES:
            raise ValueError(f'Invalid index name ({index_name}): must be one of {EMBEDDING_INDEXES}')
        if index_name not in self.indexes:
            return DummyVectorIndex(index_name=index_name)
        
        if not self.batch_writes_enabled:          
            return self.indexes[index_name].index
        else:
            return self.indexes[index_name]

    
    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        for index in self.indexes.values():
            index.write_embeddings_to_index()


    