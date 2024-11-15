# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import List, Any
from graphrag_toolkit.indexing.build.node_builder import NodeBuilder
from graphrag_toolkit.indexing.build.source_node_builder import SourceNodeBuilder
from graphrag_toolkit.indexing.build.chunk_node_builder import ChunkNodeBuilder
from graphrag_toolkit.indexing.build.topic_node_builder import TopicNodeBuilder

from llama_index.core.schema import BaseNode
from llama_index.core.bridge.pydantic import Field
from llama_index.core.schema import TransformComponent

logger = logging.getLogger(__name__)

class MetadataToNodes(TransformComponent):
    
    builders: List[NodeBuilder] = Field(
        description='Node builders'
    )
    
    def __init__(self, builders:List[NodeBuilder]=[]):

        builders = builders or self.default_builders()

        logger.debug(f'Node builders: {[type(b).__name__ for b in builders]}')

        super().__init__(
            builders=builders
        )
    
    def default_builders(self):
        return [
            SourceNodeBuilder(),
            ChunkNodeBuilder(),
            TopicNodeBuilder()
        ]
        
    @classmethod
    def class_name(cls) -> str:
        return 'MetadataToNodes'
    
    def get_nodes_from_metadata(self, input_nodes: List[BaseNode], **kwargs: Any) -> List[BaseNode]:

        results = []

        metadata_keys = [
            metadata_key
            for builder in self.builders
            for metadata_key in builder.metadata_keys()
        ]
        
        for input_node in input_nodes:
            if [key for key in metadata_keys if key in input_node.metadata]:
                
                try:

                    local_context = {}

                    for builder in self.builders:
                        output_nodes = builder.build_nodes(input_node, local_context)
                        
                        local_context[builder.name()] = output_nodes[0] if (output_nodes and len(output_nodes) == 1) else output_nodes
                        
                        for output_node in output_nodes:
                            if builder.allow_emit_node(output_node):
                                results.append(output_node)


                except Exception as e:
                    logger.exception('An error occurred while building nodes from metadata')
                    raise e
            
            results.append(input_node) # Always add the original nodes after derived nodes

        logger.debug(f'Accepted {len(input_nodes)} chunks, emitting {len(results)} nodes')

        return results
        
    def __call__(self, nodes: List[BaseNode], **kwargs: Any) -> List[BaseNode]:    
        return self.get_nodes_from_metadata(nodes, **kwargs)
                    
