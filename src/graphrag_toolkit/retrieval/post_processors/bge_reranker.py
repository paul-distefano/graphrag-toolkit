# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import torch
import logging
from pydantic import Field
from typing import List, Optional, Any, Tuple

from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle

logger = logging.getLogger(__name__)

class BGEReranker(BaseNodePostprocessor):
    """Reranks statements using the BGE reranker model."""
    
    model_name: str = Field(default='BAAI/bge-reranker-v2-minicpm-layerwise')
    gpu_id: Optional[int] = Field(default=None)
    batch_size: int = Field(default=128)
    reranker: Any = Field(default=None)
    device: Any = Field(default=None)  

    def __init__(
        self, 
        model_name: str = 'BAAI/bge-reranker-v2-minicpm-layerwise',
        gpu_id: Optional[int] = None,
        batch_size: int = 128
    ):
        super().__init__()
        try:
            from FlagEmbedding import LayerWiseFlagLLMReranker
        except ImportError:
            raise ImportError(
                "Cannot import FlagReranker package, please install it: ",
                "pip install git+https://github.com/FlagOpen/FlagEmbedding.git",
            )
        self.model_name = model_name
        self.batch_size = batch_size
        self.gpu_id = gpu_id
        
        try:
            if torch.cuda.is_available() and gpu_id is not None:
                self.device = torch.device(f'cuda:{gpu_id}')
                torch.cuda.set_device(self.device)
                torch.cuda.empty_cache()
            else:
                self.device = torch.device('cpu')
                logger.info("Using CPU for BGE reranker")
        except Exception as e:
            logger.warning(f"Failed to set GPU {gpu_id}, falling back to CPU: {str(e)}")
            self.device = torch.device('cpu')
            
        try:
            self.reranker = LayerWiseFlagLLMReranker(
                model_name,
                use_fp16=True,
                device=self.device
            )
        except Exception as e:
            logger.error(f"Failed to initialize reranker: {str(e)}")
            raise
    
    def rerank_pairs(
        self,
        pairs: List[Tuple[str, str]],
        batch_size: int = 128
    ) -> List[float]:
        """Rerank pairs without creating nodes."""
        try:
            with torch.cuda.device(self.device):
                scores = self.reranker.compute_score(
                    sentence_pairs=pairs,
                    batch_size=batch_size,
                    cutoff_layers=[28]
                )
                return scores
        except Exception as e:
            logger.error(f"Error in rerank_pairs: {str(e)}")
            raise

    def _postprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query_bundle: Optional[QueryBundle] = None,
    ) -> List[NodeWithScore]:
        if not query_bundle or not nodes:
            return nodes
            
        try:
            pairs = [(query_bundle.query_str, node.node.text) for node in nodes]

            scores = self.rerank_pairs(pairs, self.batch_size)
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            scored_nodes = [
                NodeWithScore(
                    node=node.node,
                    score=float(score) if isinstance(score, torch.Tensor) else score
                )
                for node, score in zip(nodes, scores)
            ]
            
            scored_nodes.sort(key=lambda x: x.score or 0.0, reverse=True)
            return scored_nodes
            
        except Exception as e:
            logger.error(f"BGE reranking failed: {str(e)}. Returning original nodes.")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            return nodes

    def __del__(self):
        """Cleanup when the object is deleted."""
        if torch.cuda.is_available():
            try:
                torch.cuda.empty_cache()
            except:
                pass