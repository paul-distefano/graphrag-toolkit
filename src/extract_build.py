import os

from graphrag_toolkit.storage import GraphStoreFactory
from graphrag_toolkit.storage import VectorStoreFactory
from graphrag_toolkit.indexing import sink
from graphrag_toolkit.indexing.constants import PROPOSITIONS_KEY, DEFAULT_ENTITY_CLASSIFICATIONS
from graphrag_toolkit.indexing.extract import LLMPropositionExtractor
from graphrag_toolkit.indexing.extract import TopicExtractor
from graphrag_toolkit.indexing.extract import GraphScopedValueStore
from graphrag_toolkit.indexing.extract import ScopedValueProvider, DEFAULT_SCOPE
from graphrag_toolkit.indexing.extract import ExtractionPipeline
from graphrag_toolkit.indexing.build import Checkpoint
from graphrag_toolkit.indexing.build import BuildPipeline
from graphrag_toolkit.indexing.build import VectorIndexing
from graphrag_toolkit.indexing.build import GraphConstruction

from llama_index.core.node_parser import SentenceSplitter
from llama_index.readers.web import SimpleWebPageReader
from graphrag_toolkit import set_logging_config

import nest_asyncio
import logging

nest_asyncio.apply()

set_logging_config('DEBUG')

checkpoint = Checkpoint('advanced-construction-example', enabled=True)

#graph_store = GraphStoreFactory.for_graph_store('neptune-graph://g-wyh29xm42b')
#vector_store = VectorStoreFactory.for_vector_store('neptune-graph://g-4bllscfm69')

graph_store = GraphStoreFactory.for_graph_store('neptune-db://db-neptune-pjd-graphrag-instance-1.cfotohhmiwj9.us-east-1.neptune.amazonaws.com')
vector_store = VectorStoreFactory.for_vector_store('aoss://https://fdkekmuzcfbzpruy8954.us-east-1.aoss.amazonaws.com')

# Create extraction pipeline components

# 1. Chunking using SentenceSplitter
splitter = SentenceSplitter(
    chunk_size=256,
    chunk_overlap=20
)

# 2. Proposition extraction
proposition_extractor = LLMPropositionExtractor()

# 3. Topic extraction
entity_classification_provider = ScopedValueProvider(
    label='EntityClassification',
    scoped_value_store=GraphScopedValueStore(graph_store=graph_store),
    initial_scoped_values={DEFAULT_SCOPE: DEFAULT_ENTITY_CLASSIFICATIONS}
)

topic_extractor = TopicExtractor(
    source_metadata_field=PROPOSITIONS_KEY,  # Omit this line if not performing proposition extraction
    entity_classification_provider=entity_classification_provider
    # Entity classifications saved to graph between LLM invocations
)

# Create extraction pipeline
extraction_pipeline = ExtractionPipeline.create(
    components=[
        splitter,
        proposition_extractor,
        topic_extractor
    ],
    num_workers=2,
    batch_size=4,
    checkpoint=checkpoint,
    show_progress=True
)

# Create build pipeline components
graph_construction = GraphConstruction.for_graph_store(graph_store)
vector_indexing = VectorIndexing.for_vector_store(vector_store)

# Create build pipeline
build_pipeline = BuildPipeline.create(
    components=[
        graph_construction,
        vector_indexing
    ],
    num_workers=2,
    batch_size=10,
    batch_writes_enabled=True,
    checkpoint=checkpoint,
    show_progress=True
)

# Load source documents
doc_urls = [
    'https://docs.aws.amazon.com/neptune/latest/userguide/intro.html',
    'https://docs.aws.amazon.com/neptune-analytics/latest/userguide/what-is-neptune-analytics.html',
    'https://docs.aws.amazon.com/neptune-analytics/latest/userguide/neptune-analytics-features.html',
    'https://docs.aws.amazon.com/neptune-analytics/latest/userguide/neptune-analytics-vs-neptune-database.html'
]

docs = SimpleWebPageReader(
    html_to_text=True,
    metadata_fn=lambda url: {'url': url}
).load_data(doc_urls)

# Run the build and exraction stages
docs | extraction_pipeline | build_pipeline | sink

print('Complete')