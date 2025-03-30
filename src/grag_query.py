from graphrag_toolkit import LexicalGraphQueryEngine
from graphrag_toolkit.storage import GraphStoreFactory
from graphrag_toolkit.storage import VectorStoreFactory
from graphrag_toolkit import set_logging_config

import nest_asyncio
nest_asyncio.apply()

set_logging_config('DEBUG')

#graph_store = GraphStoreFactory.for_graph_store('neptune-graph://g-wyh29xm42b')
#vector_store = VectorStoreFactory.for_vector_store('neptune-graph://g-4bllscfm69')

graph_store = GraphStoreFactory.for_graph_store('neptune-db://db-neptune-pjd-graphrag.cluster-ro-cfotohhmiwj9.us-east-1.neptune.amazonaws.com')
vector_store = VectorStoreFactory.for_vector_store('aoss://https://fdkekmuzcfbzpruy8954.us-east-1.aoss.amazonaws.com')

query_engine = LexicalGraphQueryEngine.for_traversal_based_search(
    graph_store,
    vector_store
)

response = query_engine.query("What are the differences between Neptune Database and Neptune Analytics?")

print(response.response)