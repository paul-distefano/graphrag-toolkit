# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import List, Any, Optional

from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode

from graphrag_toolkit.storage.graph_store import GraphStore
from graphrag_toolkit.storage import VectorStore
from graphrag_toolkit.retrieval.utils.statement_utils import get_top_k, SharedEmbeddingCache

logger = logging.getLogger(__name__)

class StatementCosineSimilaritySearch(BaseRetriever):
    """Retrieves statements using cosine similarity of embeddings."""

    def __init__(
        self,
        vector_store: VectorStore,
        graph_store: GraphStore,
        embedding_cache: Optional[SharedEmbeddingCache] = None,
        top_k: int = 100,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.embedding_cache = embedding_cache
        self.top_k = top_k

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        try:
            # 1. Get initial candidates from vector store via L2 Norm
            statement_results = self.vector_store.get_index('statement').top_k(
                query_bundle.query_str, 
                top_k=500
            )
            
            # 2. Get statement IDs and embeddings using shared cache
            statement_ids = [r['statement']['statementId'] for r in statement_results]
            statement_embeddings = self.embedding_cache.get_embeddings(statement_ids)

            # 3. Get top-k statements by cosine similarity
            top_k_statements = get_top_k(
                query_bundle.embedding,
                statement_embeddings,
                self.top_k
            )

            # 4. Create nodes with minimal data
            nodes = []
            for score, statement_id in top_k_statements:
                node = TextNode(
                    text="",  # Placeholder - will be populated by StatementGraphRetriever
                    metadata={
                        'statement': {'statementId': statement_id},
                        'search_type': 'cosine_similarity'
                    }
                )
                nodes.append(NodeWithScore(node=node, score=score))

            return nodes

        except Exception as e:
            logger.error(f"Error in StatementCosineSimilaritySearch: {e}")
            return []