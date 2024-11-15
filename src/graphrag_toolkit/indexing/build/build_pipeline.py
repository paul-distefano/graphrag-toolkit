# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import asyncio
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from functools import partial, reduce
from typing import Any, List, Optional, Sequence
from pipe import Pipe

from graphrag_toolkit.config import GraphRAGConfig
from graphrag_toolkit.indexing import NodeHandler
from graphrag_toolkit.indexing.build.node_builder import NodeBuilder
from graphrag_toolkit.indexing.build.checkpoint import Checkpoint, CheckpointWriter
from graphrag_toolkit.indexing.build.metadata_to_nodes import MetadataToNodes
from graphrag_toolkit.storage.constants import INDEX_KEY

from llama_index.core.async_utils import asyncio_run
from llama_index.core.utils import iter_batch
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.ingestion.pipeline import arun_transformations_wrapper
from llama_index.core.schema import TransformComponent, BaseNode

logger = logging.getLogger(__name__)

class NodeFilter(TransformComponent):
      
    def __call__(self, nodes: List[BaseNode], **kwargs: Any) -> List[BaseNode]:
        return nodes

class BuildPipeline():

    @staticmethod
    def create(components: List[TransformComponent], 
               num_workers:Optional[int]=None, 
               batch_size:Optional[int]=None, 
               batch_writes_enabled:Optional[bool]=None, 
               builders:Optional[List[NodeBuilder]]=[], 
               show_progress=False, 
               checkpoint:Optional[Checkpoint]=None
            ):
        return Pipe(
            BuildPipeline(
                components=components,
                num_workers=num_workers,
                batch_size=batch_size,
                batch_writes_enabled=batch_writes_enabled,
                builders=builders,
                show_progress=show_progress,
                checkpoint=checkpoint
            ).build
        )
    
    def __init__(self, 
                 components: List[TransformComponent], 
                 num_workers:Optional[int]=None, 
                 batch_size:Optional[int]=None, 
                 batch_writes_enabled:Optional[bool]=None, 
                 builders:Optional[List[NodeBuilder]]=[], 
                 show_progress=False, 
                 checkpoint:Optional[Checkpoint]=None
            ):
        
        components = components or []
        num_workers = num_workers or GraphRAGConfig.build_pipeline_num_workers
        batch_size = batch_size or GraphRAGConfig.build_pipeline_batch_size
        batch_writes_enabled = batch_writes_enabled or GraphRAGConfig.build_pipeline_batch_writes_enabled

        for c in components:
            if isinstance(c, NodeHandler):
                c.show_progress = show_progress

        if num_workers > multiprocessing.cpu_count():
            num_workers = multiprocessing.cpu_count()
            logger.debug(f'Setting num_workers to CPU count [num_workers: {num_workers}]')

        if checkpoint and components:
            
            l = len(components)
            for i, c in enumerate(reversed(components)):
                updated_component = checkpoint.add_writer(c)
                if isinstance(updated_component, CheckpointWriter):
                    components[l-i-1] = updated_component
                    break

        logger.debug(f'Build pipeline components: {[type(c).__name__ for c in components]}')

        self.inner_pipeline=IngestionPipeline(transformations=components, disable_cache=True)
        self.num_workers = num_workers
        self.batch_size = batch_size
        self.batch_writes_enabled = batch_writes_enabled
        self.metadata_to_nodes = MetadataToNodes(builders=builders)
        self.node_filter = NodeFilter() if not checkpoint else checkpoint.add_filter(NodeFilter())
    
    def build(self, nodes: List[BaseNode]):

        for chunks in iter_batch(nodes, (self.num_workers * self.batch_size)):
            
            (parent_batch, child_batches) = self._prepare_batches(chunks)

            if parent_batch:
                if self.inner_pipeline.transformations:
                    logger.info(f'Running build pipeline [num_jobs: 1, job_sizes: [{len(parent_batch)}], batch_size: {self.batch_size}, num_workers: {self.num_workers}]]')
                parent_batch_results = asyncio_run(
                    self._arun_pipeline(
                        self.inner_pipeline, 
                        [parent_batch], 
                        batch_writes_enabled=self.batch_writes_enabled, 
                        batch_size=self.batch_size
                    ))
                for node in parent_batch_results:
                    yield node
            
            if child_batches:
                if self.inner_pipeline.transformations:
                    logger.info(f'Running build pipeline [num_jobs: {len(child_batches)}, job_sizes: {[len(b) for b in child_batches]}, batch_size: {self.batch_size}, num_workers: {self.num_workers}]')
                child_batches_results = asyncio_run(
                    self._arun_pipeline(
                        self.inner_pipeline, 
                        child_batches, 
                        batch_writes_enabled=self.batch_writes_enabled, 
                        batch_size=self.batch_size
                    ))
                for node in child_batches_results:
                    yield node

    def _create_batches_for_chunks(self, chunks:List[BaseNode]) -> List[List[BaseNode]]:
        
        batches = []
        batch = []

        for i, c in enumerate(chunks):
            if i % self.batch_size == 0:
                if batch:
                    batches.append(batch)
                    batch = []
            nodes = self.metadata_to_nodes([c])
            batch.extend(nodes)
        if batch:
            batches.append(batch)

        return batches
    
    def _prepare_batches(self, chunks:List[BaseNode]):

        filtered_chunks = self.node_filter(chunks)
        batches = self._create_batches_for_chunks(filtered_chunks)

        node_counters = {}
        for batch in batches:
            for node in batch:
                if node.node_id not in node_counters:
                    node_counters[node.node_id] = 0
                if INDEX_KEY in node.metadata:
                    node_counters[node.node_id] += 1

        duplicates = {}
        output_batches = []

        for batch in batches:
            output_batch = []
            for node in batch:
                if node_counters[node.node_id] > 1:
                    duplicates[node.node_id] = node
                else:
                    output_batch.append(node)
            output_batches.append(output_batch)

        return (list(duplicates.values()), output_batches)


    async def _arun_pipeline(
        self,
        pipeline:IngestionPipeline,
        node_batches:List[BaseNode],
        cache_collection: Optional[str] = None,
        in_place: bool = True,
        **kwargs: Any,
    ) -> Sequence[BaseNode]:
        loop = asyncio.get_event_loop()
        with ProcessPoolExecutor(max_workers=len(node_batches)) as p:
            tasks = [
                loop.run_in_executor(
                    p,
                    partial(
                        arun_transformations_wrapper,
                        transformations=pipeline.transformations,
                        in_place=in_place,
                        cache=pipeline.cache if not pipeline.disable_cache else None,
                        cache_collection=cache_collection,
                        **kwargs
                    ),
                    batch,
                )
                for batch in node_batches
            ]
            result: List[List[BaseNode]] = await asyncio.gather(*tasks)
            nodes = reduce(lambda x, y: x + y, result, [])
        return nodes

        
