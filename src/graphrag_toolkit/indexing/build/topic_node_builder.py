# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Dict

from llama_index.core.schema import TextNode, BaseNode
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo

from graphrag_toolkit.indexing.utils.graph_utils import node_id_from
from graphrag_toolkit.indexing.build.source_node_builder import SourceNodeBuilder
from graphrag_toolkit.indexing.build.node_builder import NodeBuilder
from graphrag_toolkit.indexing.model import TopicCollection
from graphrag_toolkit.indexing.constants import TOPICS_KEY
from graphrag_toolkit.storage.constants import INDEX_KEY

class TopicNodeBuilder(NodeBuilder):
    
    @classmethod
    def name(cls) -> str:
        return 'TopicNodeBuilder'
    
    @classmethod
    def metadata_keys(cls) -> List[str]:
        return [TOPICS_KEY]
    
    def build_nodes(self, node:BaseNode, other_nodes:Dict[str, BaseNode]):
        
        chunk_id = node.node_id
        source_node = other_nodes[SourceNodeBuilder.name()]

        topic_nodes=[]
        statement_nodes=[]
        fact_nodes=[]

        data = node.metadata.get(TOPICS_KEY, [])

        if not data:
            return (topic_nodes, statement_nodes, fact_nodes)

        topics = TopicCollection.model_validate(data)

        for topic in topics.topics:
            
            topic_id = None
            
            if topic.entities or topic.statements:
                
                topic_id = node_id_from(source_node.node_id, topic.value) # topic identity defined by source, not chunk, so that we can connect same topic to multiple chunks in scope of single source
                topic.topic_id = topic_id

                for entity in topic.entities:
                    entity.entity_id = node_id_from(entity.value, entity.classification)
                
                topic_metadata = {
                    'source': source_node.metadata.get('source', {}),
                    'topic': {
                        'topicId': topic_id
                    },
                    INDEX_KEY: {
                        'index': 'topic',
                        'key': self._clean_id(topic_id)
                    }
                }

                topic_node = TextNode( # don't specify id here - each indexable topic node should be unique because topics can be associated with multiple chunks
                    text = topic.value,
                    metadata = topic_metadata,
                    excluded_embed_metadata_keys = [INDEX_KEY, 'topic'],
                    excluded_llm_metadata_keys = [INDEX_KEY, 'topic']
                )

                topic_node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(
                    node_id=chunk_id, 
                    metadata={
                        'topic': topic.model_dump()              
                    } 
                )

                topic_nodes.append(topic_node)

                prev_statement = None
                
                for statement in topic.statements:
                    
                    statement_id = node_id_from(topic_id, statement.value)
                    statement.statement_id = statement_id
                    statement.topic_id = topic_id

                    claim_metadata = {
                        'source': source_node.metadata.get('source', {}),
                        'statement': {
                            'statementId': statement_id
                        },
                        INDEX_KEY: {
                            'index': 'statement',
                            'key': self._clean_id(statement_id)
                        }
                    }

                    statement_details = '\n'.join(statement.details)

                    statement_node = TextNode(
                        id_ = statement_id,
                        text = f'{statement.value}\n\n{statement_details}' if statement_details else statement.value,
                        metadata = claim_metadata,
                        excluded_embed_metadata_keys = [INDEX_KEY, 'statement'],
                        excluded_llm_metadata_keys = [INDEX_KEY, 'statement']
                    )

                    statement_node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(
                        node_id=chunk_id, 
                        metadata={
                            'statement': statement.model_dump()              
                        } 
                    )

                    if prev_statement:
                        statement_node.relationships[NodeRelationship.PREVIOUS] = RelatedNodeInfo(
                            node_id=chunk_id, 
                            metadata={
                                'statement': prev_statement.model_dump()           
                            } 
                        ) 

                    prev_statement = statement

                    statement_nodes.append(statement_node)
            
                    for fact in statement.facts:

                        fact_value = self._format_fact(
                            fact.subject.value,
                            fact.subject.classification,
                            fact.predicate.value,
                            fact.object.value if fact.object else fact.complement,
                            fact.object.classification if fact.object else None
                        )
                        
                        fact_id = node_id_from(fact_value)

                        fact.fact_id = fact_id
                        fact.statement_id = statement_id

                        fact.subject.entity_id = node_id_from(fact.subject.value, fact.subject.classification)
                        if fact.object:
                            fact.object.entity_id = node_id_from(fact.object.value, fact.object.classification)
                        
                        fact_metadata = {
                            'fact': {
                                'factId': fact_id
                            },
                            INDEX_KEY: {
                                'index': 'fact',
                                'key': self._clean_id(fact_id)
                            }
                        }

                        fact_node = TextNode( # don't specify id here - each indexable fact node should be unique because facts can be associated with multiple claims
                            text = fact_value,
                            metadata = fact_metadata,
                            excluded_embed_metadata_keys = [INDEX_KEY, 'fact'],
                            excluded_llm_metadata_keys = [INDEX_KEY, 'fact']
                        )

                        fact_node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(
                            node_id=chunk_id, 
                            metadata={
                                'fact': fact.model_dump()              
                            } 
                        )

                        fact_nodes.append(fact_node)

        results = []

        results.extend(topic_nodes)
        results.extend(statement_nodes)
        results.extend(fact_nodes)
        
        return results

    
