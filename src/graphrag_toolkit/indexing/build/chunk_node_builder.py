# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Dict

from llama_index.core.schema import BaseNode, TextNode

from graphrag_toolkit.indexing.build.source_node_builder import SourceNodeBuilder
from graphrag_toolkit.indexing.build.node_builder import NodeBuilder
from graphrag_toolkit.indexing.constants import TOPICS_KEY
from graphrag_toolkit.storage.constants import INDEX_KEY

class ChunkNodeBuilder(NodeBuilder):
    
    @classmethod
    def name(cls) -> str:
        return 'ChunkNodeBuilder'
    
    @classmethod
    def metadata_keys(cls) -> List[str]:
        return [TOPICS_KEY]
    
    def build_nodes(self, node:BaseNode, other_nodes:Dict[str, BaseNode]):
        
        chunk_id = node.node_id
        chunk_node = node.model_copy()
        
        topics = [topic['value'] for topic in node.metadata.get(TOPICS_KEY, {}).get('topics', [])]

        metadata = {
            'chunk': {
                'chunkId': chunk_id  
            },
            'topics': topics 
        }

        source_node = other_nodes.get(SourceNodeBuilder.name(), None)
        
        if source_node:
            metadata['source'] = source_node.metadata['source']
        
        metadata[INDEX_KEY] = {
            'index': 'chunk',
            'key': self._clean_id(chunk_id)
        }

        chunk_node.metadata = metadata
        chunk_node.excluded_embed_metadata_keys = [INDEX_KEY, 'chunk']
        chunk_node.excluded_llm_metadata_keys = [INDEX_KEY, 'chunk']
        
        return [chunk_node]
    
    

    
