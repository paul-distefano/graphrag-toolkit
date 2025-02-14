# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import List

from llama_index.core.schema import TextNode, BaseNode
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo

from graphrag_toolkit.indexing.build.filter import Filter
from graphrag_toolkit.indexing.utils.graph_utils import node_id_from
from graphrag_toolkit.indexing.build.node_builder import NodeBuilder
from graphrag_toolkit.indexing.model import TopicCollection
from graphrag_toolkit.indexing.constants import TOPICS_KEY
from graphrag_toolkit.storage.constants import INDEX_KEY

class StatementNodeBuilder(NodeBuilder):
    
    @classmethod
    def name(cls) -> str:
        return 'StatementNodeBuilder'
    
    @classmethod
    def metadata_keys(cls) -> List[str]:
        return [TOPICS_KEY]
    
    def build_nodes(self, nodes:List[BaseNode], filter:Filter):

        statement_nodes = {}
        fact_nodes = {}

        for node in nodes:

            chunk_id = node.node_id

            data = node.metadata.get(TOPICS_KEY, [])
            
            if not data:
                continue

            topics = TopicCollection.model_validate(data)

            source_info = node.relationships[NodeRelationship.SOURCE]
            source_id = source_info.node_id

            source_metadata = {
                'sourceId': source_id
            }

            if source_info.metadata:
                source_metadata['metadata'] = source_info.metadata

            for topic in topics.topics:

                topic_id = node_id_from(source_id, topic.value) # topic identity defined by source, not chunk, so that we can connect same topic to multiple chunks in scope of single source

                prev_statement = None
                
                for statement in topic.statements:

                    if filter.ignore_statement(statement.value):
                        continue

                    statement_id = node_id_from(topic_id, statement.value)
     
                    if statement_id not in statement_nodes:

                        statement.statementId = statement_id
                        statement.topicId = topic_id    
                        statement.chunkId = chunk_id
                        
                        statement_metadata = {
                            'source': source_metadata,
                            'statement': statement.model_dump(),
                            INDEX_KEY: {
                                'index': 'statement',
                                'key': self._clean_id(statement_id)
                            }
                        }

                        statement_details = '\n'.join(statement.details)

                        statement_node = TextNode(
                            id_ = statement_id,
                            text = f'{statement.value}\n\n{statement_details}' if statement_details else statement.value,
                            metadata = statement_metadata,
                            excluded_embed_metadata_keys = [INDEX_KEY, 'statement'],
                            excluded_llm_metadata_keys = [INDEX_KEY, 'statement']
                        )

                        if prev_statement:
                            statement_node.relationships[NodeRelationship.PREVIOUS] = RelatedNodeInfo(
                                node_id=prev_statement.statementId,
                                metadata={
                                    'statement': prev_statement.model_dump()
                                }
                            ) 

                        prev_statement = statement

                        statement_nodes[statement_id] = statement_node
            
                    for fact in statement.facts:

                        fact_value = self._format_fact(
                            fact.subject.value,
                            fact.subject.classification,
                            fact.predicate.value,
                            fact.object.value if fact.object else fact.complement,
                            fact.object.classification if fact.object else None
                        )
                        
                        fact_id = node_id_from(fact_value)

                        lookup_id = f'{statement_id}-{fact_id}'

                        if lookup_id not in fact_nodes:

                            fact.factId = fact_id
                            fact.statementId = statement_id

                            fact.subject.entityId = node_id_from(fact.subject.value, fact.subject.classification)
                            if fact.object:
                                fact.object.entityId = node_id_from(fact.object.value, fact.object.classification)
                            
                            fact_metadata = {
                                'fact': fact.model_dump(),
                                INDEX_KEY: {
                                    'index': 'fact',
                                    'key': self._clean_id(fact_id)
                                }
                            }

                            fact_node = TextNode( # don't specify id here - each fact node should be indexable because facts can be associated with multiple statements
                                text = fact_value,
                                metadata = fact_metadata,
                                excluded_embed_metadata_keys = [INDEX_KEY, 'fact'],
                                excluded_llm_metadata_keys = [INDEX_KEY, 'fact']
                            )

                            fact_nodes[lookup_id] = fact_node

        results = []

        results.extend(statement_nodes.values())
        results.extend(fact_nodes.values())
        
        return results
