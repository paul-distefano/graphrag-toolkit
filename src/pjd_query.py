from graphrag_toolkit import LexicalGraphQueryEngine
from graphrag_toolkit.storage import GraphStoreFactory
from graphrag_toolkit.storage import VectorStoreFactory
from graphrag_toolkit import set_logging_config
from graphrag_toolkit.retrieval.prompts import ANSWER_QUESTION_USER_PROMPT

from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core import QueryBundle
from llama_index.core.schema import NodeWithScore

from typing import List
import nest_asyncio

from pjd_prompts import NO_RAG_ANSWER_QUESTION_SYSTEM_PROMPT

nest_asyncio.apply()

class EmptyRetriever(BaseRetriever):

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        return []

set_logging_config('DEBUG')

graph_store = GraphStoreFactory.for_graph_store('neptune-db://db-neptune-pjd-graphrag.cluster-ro-cfotohhmiwj9.us-east-1.neptune.amazonaws.com')
vector_store = VectorStoreFactory.for_vector_store('aoss://https://fdkekmuzcfbzpruy8954.us-east-1.aoss.amazonaws.com')

query_engine = LexicalGraphQueryEngine(
    graph_store,
    vector_store,
    None,
    NO_RAG_ANSWER_QUESTION_SYSTEM_PROMPT,
    ANSWER_QUESTION_USER_PROMPT,
    EmptyRetriever(None)
)

response = query_engine.query("What are the differences between Neptune Database and Neptune Analytics?")

print(response.response)
