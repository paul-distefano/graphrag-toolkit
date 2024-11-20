# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
from lru import LRU

from graphrag_toolkit.indexing.model import Topic
from graphrag_toolkit.storage.graph_store import GraphStore
from graphrag_toolkit.indexing.build.graph_builder import GraphBuilder

from llama_index.core.schema import BaseNode
from llama_index.core.schema import NodeRelationship

logger = logging.getLogger(__name__)

class TopicGraphBuilder(GraphBuilder):
    
    @classmethod
    def index_key(cls) -> str:
        return 'topic'
    
    def build(self, node:BaseNode, graph_client: GraphStore, node_ids:LRU):
            
        topic_metadata = node.metadata.get('topic', {})
        topic_id = topic_metadata.get('topicId', None)

        if topic_id:
        
            logger.debug(f'Inserting topic [topic_id: {topic_id}]')

            statements = [
                '// insert topics',
                'UNWIND $params AS params'
            ]

            source_info = node.relationships.get(NodeRelationship.SOURCE, None)
            topic = Topic.model_validate(source_info.metadata.get('topic', None))
            
            if topic:

                chunk_id = source_info.node_id

                
                statements.extend([
                    f'MERGE (topic:Topic{{{graph_client.node_id("topicId")}: params.topic_id}})',
                    'ON CREATE SET topic.value=params.title ON MATCH SET topic.value=params.title',
                    'WITH topic, params',
                    f'MERGE (chunk:Chunk{{{graph_client.node_id("chunkId")}: params.chunk_id}})',
                    'MERGE (topic)-[:MENTIONED_IN]->(chunk)'
                ])

                properties = {
                    'topic_id': topic_id,
                    'title': topic.value,
                    'chunk_id': chunk_id
                }

                query = '\n'.join(statements)

                graph_client.execute_query_with_retry(query, self._to_params(properties))

        else:
            logger.warning(f'topic_id missing from topic node [node_id: {node.node_id}]') 
