# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Dict

from llama_index.core.schema import BaseNode

from graphrag_toolkit.indexing.build.source_node_builder import SourceNodeBuilder
from graphrag_toolkit.indexing.build.node_builder import NodeBuilder
from graphrag_toolkit.indexing.constants import TRIPLES_KEY
from graphrag_toolkit.storage.constants import INDEX_KEY

class ChunkNodeBuilder(NodeBuilder):
    
    @classmethod
    def name(cls) -> str:
        return 'ChunkNodeBuilder'
    
    @classmethod
    def metadata_keys(cls) -> List[str]:
        return [TRIPLES_KEY]
    
    def build_nodes(self, node:BaseNode, other_nodes:Dict[str, BaseNode]):
        
        chunk_id = node.node_id
        
        chunk_node = node.copy()
        
        topics = [topic['value'] for topic in node.metadata.get(TRIPLES_KEY, {}).get('topics', [])]

        metadata = {
            'chunk': {
                'chunkId': chunk_id,
                'topics': topics
            }  
        }

        source_node = other_nodes.get(SourceNodeBuilder.name(), None)
        
        if source_node:
            metadata['source'] = source_node.metadata['source']
        
        metadata[INDEX_KEY] = {
            'index': 'chunk',
            'key': self._clean_id(chunk_id)
        }
        
        chunk_node.metadata = metadata
        chunk_node.excluded_embed_metadata_keys = [INDEX_KEY]
        chunk_node.excluded_llm_metadata_keys = [INDEX_KEY]
        
        return [chunk_node]
    
    

    
