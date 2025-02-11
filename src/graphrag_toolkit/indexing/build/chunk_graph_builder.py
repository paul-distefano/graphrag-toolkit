# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging

from graphrag_toolkit.storage.graph_store import GraphStore
from graphrag_toolkit.indexing.build.graph_builder import GraphBuilder

from llama_index.core.schema import BaseNode
from llama_index.core.schema import NodeRelationship

logger = logging.getLogger(__name__)

class ChunkGraphBuilder(GraphBuilder):
    
    @classmethod
    def index_key(cls) -> str:
        return 'chunk'
    
    def build(self, node:BaseNode, graph_client: GraphStore):
            
        chunk_metadata = node.metadata.get('chunk', {})
        chunk_id = chunk_metadata.get('chunkId', None)

        if chunk_id:

            logger.debug(f'Inserting chunk [chunk_id: {chunk_id}]')

            statements = [
                '// insert chunks',
                'UNWIND $params AS params'
            ]

            statements.extend([
                f'MERGE (chunk:Chunk{{{graph_client.node_id("chunkId")}: params.chunk_id}})',
                'ON CREATE SET chunk.value = params.text ON MATCH SET chunk.value = params.text'
            ])
            
            source_info = node.relationships.get(NodeRelationship.SOURCE, None)

            if source_info:
                
                source_id = source_info.node_id

                statements.extend([
                    f'MERGE (source:Source{{{graph_client.node_id("sourceId")}: params.source_id}})',
                    'MERGE (chunk)-[:EXTRACTED_FROM]->(source)'
                ])

                properties = {
                    'chunk_id': chunk_id,
                    'source_id': source_id,
                    'text': node.text
                }
            else:
                logger.warning(f'source_id missing from chunk node [node_id: {chunk_id}]')
            
            key_index = 0
            
            for node_relationship,relationship_info in node.relationships.items():
                
                key_index += 1
                key = f'node_relationship_{key_index}'
                node_id = relationship_info.node_id
                properties[key] = node_id

                if node_relationship == NodeRelationship.PARENT:
                    statements.append(f'MERGE (parent:Chunk{{{graph_client.node_id("chunkId")}: params.{key}}})')
                    statements.append('MERGE (chunk)-[:PARENT]->(parent)')
                if node_relationship == NodeRelationship.CHILD:
                    statements.append(f'MERGE (child:Chunk{{{graph_client.node_id("chunkId")}: params.{key}}})')
                    statements.append('MERGE (chunk)-[:CHILD]->(child)')
                elif node_relationship == NodeRelationship.PREVIOUS:
                    statements.append(f'MERGE (previous:Chunk{{{graph_client.node_id("chunkId")}: params.{key}}})')
                    statements.append('MERGE (chunk)-[:PREVIOUS]->(previous)')
                elif node_relationship == NodeRelationship.NEXT:
                    statements.append(f'MERGE (next:Chunk{{{graph_client.node_id("chunkId")}: params.{key}}})')
                    statements.append('MERGE (chunk)-[:NEXT]->(next)')
                            
            query = '\n'.join(statements)

            graph_client.execute_query_with_retry(query, self._to_params(properties), max_attempts=5, max_wait=7)

        else:
            logger.warning(f'chunk_id missing from chunk node [node_id: {node.node_id}]')