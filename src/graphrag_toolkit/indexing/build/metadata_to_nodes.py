# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import List, Any
from graphrag_toolkit.indexing.build.build_filter import BuildFilter
from graphrag_toolkit.indexing.build.node_builder import NodeBuilder
from graphrag_toolkit.indexing.build.source_node_builder import SourceNodeBuilder
from graphrag_toolkit.indexing.build.chunk_node_builder import ChunkNodeBuilder
from graphrag_toolkit.indexing.build.topic_node_builder import TopicNodeBuilder
from graphrag_toolkit.indexing.build.statement_node_builder import StatementNodeBuilder

from llama_index.core.schema import BaseNode

logger = logging.getLogger(__name__)

class MetadataToNodes():

    def __init__(self, builders:List[NodeBuilder]=[], filter:BuildFilter=None):

        self.builders = builders or self.default_builders()
        self.filter = filter or BuildFilter()

        logger.debug(f'Node builders: {[type(b).__name__ for b in self.builders]}')
    
    def default_builders(self):
        return [
            SourceNodeBuilder(),
            ChunkNodeBuilder(),
            TopicNodeBuilder(),
            StatementNodeBuilder()
        ]
        
    @classmethod
    def class_name(cls) -> str:
        return 'MetadataToNodes'
    
    def get_nodes_from_metadata(self, input_nodes: List[BaseNode], **kwargs: Any) -> List[BaseNode]:
        
        def clean_text(node):
            node.text = node.text.replace('\x00', '')
            return node

        results = []

        for builder in self.builders:
            try:
                
                filtered_input_nodes = [
                    clean_text(node) 
                    for node in input_nodes 
                    if any(key in builder.metadata_keys() for key in node.metadata)
                ]
                
                results.extend(builder.build_nodes(filtered_input_nodes, self.filter))
            except Exception as e:
                    logger.exception('An error occurred while building nodes from metadata')
                    raise e
            
        results.extend(input_nodes) # Always add the original nodes after derived nodes    

        logger.debug(f'Accepted {len(input_nodes)} chunks, emitting {len(results)} nodes')

        return results
        
    def __call__(self, nodes: List[BaseNode], **kwargs: Any) -> List[BaseNode]:    
        return self.get_nodes_from_metadata(nodes, **kwargs)
                    
