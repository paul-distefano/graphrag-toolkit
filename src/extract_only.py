
import os

from graphrag_toolkit import LexicalGraphIndex
from graphrag_toolkit.storage import GraphStoreFactory
from graphrag_toolkit.storage import VectorStoreFactory
from graphrag_toolkit.indexing.load import FileBasedDocs
from graphrag_toolkit.indexing.build import Checkpoint
from graphrag_toolkit import set_logging_config
import logging

from llama_index.readers.web import SimpleWebPageReader

import nest_asyncio
nest_asyncio.apply()

extracted_docs = FileBasedDocs(
    docs_directory='extracted'
)

set_logging_config('DEBUG')

checkpoint = Checkpoint('extraction-checkpoint')

graph_store = GraphStoreFactory.for_graph_store('neptune-graph://g-wyh29xm42b')
vector_store = VectorStoreFactory.for_vector_store('neptune-graph://g-4bllscfm69')

graph_index = LexicalGraphIndex(
    graph_store,
    vector_store
)

doc_urls = [
    'https://docs.aws.amazon.com/neptune/latest/userguide/intro.html',
    'https://docs.aws.amazon.com/neptune-analytics/latest/userguide/what-is-neptune-analytics.html',
    'https://docs.aws.amazon.com/neptune-analytics/latest/userguide/neptune-analytics-features.html',
    'https://docs.aws.amazon.com/neptune-analytics/latest/userguide/neptune-analytics-vs-neptune-database.html'
]

docs = SimpleWebPageReader(
    html_to_text=True,
    metadata_fn=lambda url:{'url': url}
).load_data(doc_urls)

graph_index.extract(docs, handler=extracted_docs, checkpoint=checkpoint, show_progress=True)

collection_id = extracted_docs.collection_id

print('Extraction complete')
print(f'collection_id: {collection_id}')
