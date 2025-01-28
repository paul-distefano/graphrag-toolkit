# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
from pipe import Pipe
from typing import List, Optional, Sequence, Dict, Iterable

from graphrag_toolkit.config import GraphRAGConfig
from graphrag_toolkit.indexing.model import SourceType, SourceDocument, source_documents_from_source_types
from graphrag_toolkit.indexing.extract.pipeline_decorator import PipelineDecorator
from graphrag_toolkit.indexing.build.checkpoint import Checkpoint
from graphrag_toolkit.indexing.extract.docs_to_nodes import DocsToNodes
from graphrag_toolkit.indexing.extract.id_rewriter import IdRewriter
from graphrag_toolkit.indexing.constants import SOURCE_DOC_KEY

from llama_index.core.node_parser import TextSplitter
from llama_index.core.async_utils import asyncio_run
from llama_index.core.utils import iter_batch
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.extractors.interface import BaseExtractor
from llama_index.core.schema import TransformComponent
from llama_index.core.schema import BaseNode
from llama_index.core.schema import NodeRelationship

logger = logging.getLogger(__name__)
    
class PassThroughDecorator(PipelineDecorator):
    def __init__(self):
        pass
    
    def handle_input_docs(self, nodes:Iterable[SourceDocument]):
        return nodes
    
    def handle_output_doc(self, node: SourceDocument) -> SourceDocument:
        return node


class ExtractionPipeline():

    @staticmethod
    def create(components: List[TransformComponent], 
               extraction_decorator:PipelineDecorator=None, 
               num_workers=None, 
               batch_size=None, 
               show_progress=False, 
               checkpoint:Optional[Checkpoint]=None):
        
        return Pipe(
            ExtractionPipeline(
                components=components, 
                extraction_decorator=extraction_decorator,
                num_workers=num_workers,
                batch_size=batch_size,
                show_progress=show_progress,
                checkpoint=checkpoint
            ).extract
        )
    
    def __init__(self, 
                 components: List[TransformComponent], 
                 extraction_decorator:PipelineDecorator=None, 
                 num_workers=None, 
                 batch_size=None, 
                 show_progress=False, 
                 checkpoint:Optional[Checkpoint]=None):
        
        components = components or []
        num_workers = num_workers or GraphRAGConfig.extraction_num_workers
        batch_size = batch_size or GraphRAGConfig.extraction_batch_size

        for c in components:
            if isinstance(c, BaseExtractor):
                c.show_progress = show_progress

        def add_id_rewriter(c):
            if isinstance(c, TextSplitter):
                logger.debug(f'Wrapping {type(c).__name__} with IdRewriter')
                return IdRewriter(inner=c)
            else:
                return c
            
        components = [add_id_rewriter(c) for c in components]
        
        if not any([isinstance(c, IdRewriter) for c in components]):
            logger.debug(f'Adding DocToNodes to components')
            components.insert(0, IdRewriter(inner=DocsToNodes()))
            
        if checkpoint:
            components = [checkpoint.add_filter(c) for c in components]

        logger.debug(f'Extract pipeline components: {[type(c).__name__ for c in components]}')

        self.ingestion_pipeline = IngestionPipeline(transformations=components)
        self.extraction_decorator = extraction_decorator or PassThroughDecorator()
        self.num_workers = num_workers
        self.batch_size = batch_size
        self.show_progress = show_progress
        self.id_rewriter = IdRewriter()
    
    def _source_documents_from_base_nodes(self, nodes:Sequence[BaseNode]) -> List[SourceDocument]:
        results:Dict[str, SourceDocument] = {}
        
        for node in nodes:
            source_info = node.relationships[NodeRelationship.SOURCE]
            source_id = source_info.node_id
            if source_id not in results:
                results[source_id] = SourceDocument()
            results[source_id].nodes.append(node)

        return list(results.values())
    
    def extract(self, inputs: Iterable[SourceType]):

        input_source_documents = source_documents_from_source_types(inputs)

        for source_documents in iter_batch(input_source_documents, self.batch_size):

            source_documents = self.id_rewriter.handle_source_docs(source_documents)
            source_documents = self.extraction_decorator.handle_input_docs(source_documents)

            input_nodes = [
                n
                for sd in source_documents
                for n in sd.nodes
            ]

            logger.info(f'Running extraction pipeline [batch_size: {self.batch_size}, num_workers: {self.num_workers}]')
            
            output_nodes = asyncio_run(self.ingestion_pipeline.arun(nodes=input_nodes, num_workers=self.num_workers, show_progress=self.show_progress))

            output_source_documents = self._source_documents_from_base_nodes(output_nodes)
            
            for source_document in output_source_documents:
                yield self.extraction_decorator.handle_output_doc(source_document)
                
