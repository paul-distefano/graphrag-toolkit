# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Dict, Optional, Any
from lru import LRU

from llama_index.core.schema import TextNode, BaseNode
from llama_index.core.schema import NodeRelationship
from llama_index.core.bridge.pydantic import Field, PrivateAttr

from graphrag_toolkit.indexing.build.node_builder import NodeBuilder
from graphrag_toolkit.indexing.constants import TOPICS_KEY
from graphrag_toolkit.storage.constants import INDEX_KEY

class SourceNodeBuilder(NodeBuilder):
    
    @classmethod
    def name(cls) -> str:
        return 'SourceNodeBuilder'
    
    @classmethod
    def metadata_keys(cls) -> List[str]:
        return [TOPICS_KEY]
    
    _source_node_cache: Optional[Any] = PrivateAttr(default=None)
    
    def __getstate__(self):
        self._source_node_cache = None
        return super().__getstate__()

    @property
    def source_node_cache(self):
        if self._source_node_cache is None:
            self._source_node_cache = LRU(1000)
        return self._source_node_cache
    
    def build_nodes(self, node:BaseNode, other_nodes:Dict[str, BaseNode]):
        source_info = node.relationships.get(NodeRelationship.SOURCE, None)

        if not source_info:
            return []
            
        source_id = source_info.node_id
        
        metadata = {
            'source': {
                'sourceId': source_id
            }
        }
        
        if source_info.metadata:
            metadata['source']['metadata'] = source_info.metadata
            
        metadata[INDEX_KEY] = {
            'index': 'source',
            'key': self._clean_id(source_id)
        }
        
        return [TextNode(
            id_ = source_id,
            metadata = metadata,
            excluded_embed_metadata_keys = [INDEX_KEY],
            excluded_llm_metadata_keys = [INDEX_KEY]
        )]
    
    def allow_emit_node(self, node:BaseNode) -> bool:
        if node and not self.source_node_cache.has_key(node.node_id):
            self.source_node_cache[node.node_id] = None
            return True
        else:
            return False


    
