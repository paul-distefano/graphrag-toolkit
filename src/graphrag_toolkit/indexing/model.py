# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Union, Dict

from llama_index.core.schema import TextNode, Document, BaseNode
from llama_index.core.schema import NodeRelationship

class SourceDocument(BaseModel):
    model_config = ConfigDict(strict=True)
    
    refNode:Optional[BaseNode]=None
    nodes:List[BaseNode]=[]

    def source_id(self):
        if not self.nodes:
            return None
        return self.nodes[0].relationships[NodeRelationship.SOURCE].node_id


SourceType = Union[SourceDocument, BaseNode]

def source_documents_from_source_types(inputs: List[SourceType]) -> List[SourceDocument]:

    results:List[SourceDocument] = []
    chunks_by_source:Dict[str, SourceDocument] = {}

    for input in inputs:
        if isinstance(input, SourceDocument):
            results.append(input)
        elif isinstance(input, Document):
            results.append(SourceDocument(nodes=[input]))
        elif isinstance(input, TextNode):
            source_info = input.relationships[NodeRelationship.SOURCE]
            source_id = source_info.node_id
            if source_id not in chunks_by_source:
                chunks_by_source[source_id] = SourceDocument()
            chunks_by_source[source_id].nodes.append(input)
        else:
            raise ValueError(f'Unexpected source type: {type(input)}')

    results.extend([
        SourceDocument(nodes=list(nodes)) for nodes in chunks_by_source.values()
    ])

    return results


class Propositions(BaseModel):
    model_config = ConfigDict(strict=True)
    
    propositions: List[str]

class Entity(BaseModel):
    model_config = ConfigDict(strict=True)
    
    entityId: Optional[str]=None

    value: str
    classification: Optional[str]=None

class Relation(BaseModel):
    model_config = ConfigDict(strict=True)

    value: str

class Fact(BaseModel):
    model_config = ConfigDict(strict=True)

    factId: Optional[str]=None
    statementId: Optional[str]=None

    subject: Entity
    predicate: Relation
    object: Optional[Entity]=None
    complement: Optional[str]=None

class Statement(BaseModel):
    model_config = ConfigDict(strict=True)

    statementId: Optional[str]=None
    topicId: Optional[str]=None
    chunkId: Optional[str]=None

    value: str
    details: List[str]=[]
    facts: List[Fact]=[]

class Topic(BaseModel):
    model_config = ConfigDict(strict=True)

    topicId : Optional[str]=None
    chunkIds: List[str]=[]

    value: str
    entities: List[Entity]=[]
    statements: List[Statement]=[]

class TopicCollection(BaseModel):
    model_config = ConfigDict(strict=True)

    topics: List[Topic]=[]  
