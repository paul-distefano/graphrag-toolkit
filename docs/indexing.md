[[Home](./)]

## Indexing

There are two stages to indexing: extract, and build. The graphrag-toolkit uses separate pipelines for each of these stages, plus micro-batching, to provide a continous ingest capability. This means that your graph will start being populated soon after extraction begins.

You can run the extract and build pipelines together, to provide for the continuous ingest described above. Or you can run the two pipelines separately, extracting first to file-based chunks, and then later building a graph from these chunks.

The `LexicalGraphIndex` is a convenience class that allows you to run the extract and build pipelines together or separately. Alternatively, you can build your graph construction application using the underlying pipelines. This gives you more control over the configuration of each stage. We describe these two different approaches in the [Using the LexicalGraphIndex to construct a graph](#using-the-lexicalgraphindex-to-construct-a-graph) and [Advanced graph construction](#advanced-graph-construction) sections below.

#### Extract

The extraction stage is, by default, a three-step process: 

  1. The source documents are broken down into chunks.
  2. For each chunk, an LLM extracts a set of propositions from the unstructured content. This proposition extraction helps 'clean' the content and improve the subsequent entity/topic/statement/fact extraction by breaking complex sentences into simpler sentences, replacing pronouns with specific names, and replacing acronyms where possible. These propositions are added to the chunk's metadata under the `aws::graph::propositions` key.
  3. Following the proposition extraction, a second LLM call extracts entities, relations, topics, statements and facts from the set of extracted propositions. These details are added to the chunk's metadata under the `aws::graph::topics` key.
  
Only the third step here is mandatory. If your source data has already been chunked (you're importing from an Amazon Bedrock Knowledge Base, for example), you can omit step 1. If you're willing to trade a reduction in LLM calls and improved performance for a reduction in the quality of the entity/topic/statement/fact extraction, you can omit step 2.

Extraction uses a lightly guided strategy whereby the extraction process is seeded with a list of preferred entity classifications. The LLM is instructed to use an existing classification from the list before creating new ones. Any new classifications introduced by the LLM are then carried forward to subsequent invocations. This approach reduces but doesn't eliminate unwanted variations in entity classification.

The list of `DEFAULT_ENTITY_CLASSIFICATIONS` used to seed the extraction process can be found [here](https://github.com/awslabs/graphrag-toolkit/blob/main/src/graphrag_toolkit/indexing/extract/constants.py). If these classifications are not appropriate to your worklaod you can replace them (see the [Configuring the extract and build stages](#configuring-the-extract-and-build-stages) and [Advanced graph construction](#advanced-graph-construction) sections below).

Relationship values are currently unguided (though relatively concise).

#### Build

In the build stage, the LlamaIndex chunk nodes emitted from the extract stage are broken down further into a stream of individual source, chunk, topic, statement and fact LlamaIndex nodes. Graph construction and vector indexing handlers process these nodes to build and index the graph content. Each of these nodes has an `aws::graph::index` metadata item containing data that can be used to index the node in a vector store (though only the chunk and statement nodes are actually indexed in the current implementation).

### Using the LexicalGraphIndex to construct a graph

The `LexicalGraphIndex` provides a convenient means of constructing a graph – via either continuous ingest, or separate extract and build stages. When constructing a `LexicalGraphIndex` you must supply a graph store and a vector store (see [Storage Model](./storage-model.md) for more details). In the examples below, the graph store and vector store connection strings are fetched from environment variables.

The `LexicalGraphIndex` constructor has an `extraction_dir` named argument. This is the path to a local directory to which intermediate artefacts (such as [checkpoints](#checkpoints)) will be written. By default, the vaue of `extraction_dir` is set to 'output'.

#### Continous ingest using extract_and_build

Use `LexicalGraphIndex.extract_and_build()` to extract and build a graph in a manner that supports continous ingest. 

The extraction stage consumes LlamaIndex nodes – either documents, which will be chunked during extraction, or pre-chunked text nodes. Use a LlamaIndex reader to [load source documents](https://docs.llamaindex.ai/en/stable/understanding/loading/loading/). The example below uses a LlamaIndex `SimpleWebReader` to load several HTML pages.

```
import os

from graphrag_toolkit import LexicalGraphIndex
from graphrag_toolkit.storage import GraphStoreFactory
from graphrag_toolkit.storage import VectorStoreFactory

from llama_index.readers.web import SimpleWebPageReader

import nest_asyncio
nest_asyncio.apply()

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

graph_store = GraphStoreFactory.for_graph_store(os.environ['GRAPH_STORE'])
vector_store = VectorStoreFactory.for_vector_store(os.environ['VECTOR_STORE'])

graph_index = LexicalGraphIndex(
    graph_store, 
    vector_store
)

graph_index.extract_and_build(docs)
```

#### Run the extract and build stages separately

Using the `LexicalGraphIndex` you can perform the extract and build stages separately. This is useful if you want to extract the graph once, and then build it multiple times (in different environments, for example.)

When you run the extract and build stages separately, you can persist the extracted chunks to the filesystem in at the end of the extract stage, and then consume these same chunks in the build stage. Use the graphrag_toolkit's `FileBasedChunks` class to persist and then retrieve JSON-serialized LlamaIndex nodes.

The following example shows how to use a `FileBaseChunks` handler to persist extracted chunks to the filesystem at the end of the extract stage:

```
from graphrag_toolkit import LexicalGraphIndex
from graphrag_toolkit.storage import GraphStoreFactory
from graphrag_toolkit.storage import VectorStoreFactory
from graphrag_toolkit.indexing.load import FileBasedChunks

from llama_index.readers.web import SimpleWebPageReader

import nest_asyncio
nest_asyncio.apply()

file_based_chunks = FileBasedChunks('./extracted/')

graph_store = GraphStoreFactory.for_graph_store(graph_store_info)
vector_store = VectorStoreFactory.for_vector_store(vector_store_info)

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

graph_index.extract(docs, handler=file_based_chunks)
```

Following the extract stage, you can then build the graph from the previously extracted chunks. Whereas in the extract stage the `FileBasedChunks` object acted as a handler to persist extracted chunks, in the build stage the `FileBasedChunks` object acts as a source of LlamaIndex nodes, and is thus passed as the first argument to the `build()` method:

```
from graphrag_toolkit import LexicalGraphIndex
from graphrag_toolkit.storage import GraphStoreFactory
from graphrag_toolkit.storage import VectorStoreFactory
from graphrag_toolkit.indexing.load import FileBasedChunks

import nest_asyncio
nest_asyncio.apply()

file_based_chunks = FileBasedChunks('./extracted/')

graph_store = GraphStoreFactory.for_graph_store(graph_store_info)
vector_store = VectorStoreFactory.for_vector_store(vector_store_info)

graph_index = LexicalGraphIndex(
    graph_store, 
    vector_store
)

graph_index.build(file_based_chunks)
```

#### Configuring the extract and build stages

You can configure the number of workers and batch sizes for extarct and build stages of the `LexicalGraphIndex` using the `GraphRAGConfig` object. See [Configuration](./configuration.md) for more details on using the configuration object. 

Besides configuring the workers and batch sizes, you can also configure the extraction process with regard to chunking, proposition extraction and entity classification by passing an instance of `ExtractionConfig` to the `LexicalGraphIndex` constructor:

```
from graphrag_toolkit import LexicalGraphIndex, ExtractionConfig

...

graph_index = LexicalGraphIndex(
    graph_store, 
    vector_store,
    extraction_config = ExtractionConfig(
      enable_chunking=False,
      enable_proposition_extraction=False
    )
)
```

The `ExtractionConfig` object has the following parameters.

| Parameter  | Description | Default Value |
| ------------- | ------------- | ------------- |
| `enable_chunking` | Chunk the source data using a LlamaIndex `SentenceSplitter` | `True` |
| `chunk_size` | Token chunk size for each chunk if using the `SentenceSplitter` | `256` |
| `chunk_overlap` | Token overlap of each chunk when splitting if using the `SentenceSplitter` | `20` |
| `enable_proposition_extraction` | Perform proposition extraction before extracting topics, statements, facts and entities | `True` |
| `preferred_entity_classifications` | Comma-separated list of preferred entity classifications used to seed the entity extraction | `DEFAULT_ENTITY_CLASSIFICATIONS` |


#### Checkpoints

The graphrag-toolkit retries upsert operations and calls to LLMs and embedding models that don't succeed. However, failures can still happen. If an extract or build stage fails partway through, you typically don't want to reprocess chunks that have successfully made their way through the entire graph construction pipeline.

To avoid having to reprocess chunks that have been successfully processed in a previous run, provide a `Checkpoint` instance to the `extract_and_build()`, `extract()` and/or `build()` methods. A checkpoint adds a checkpoint *filter* to steps in the extract and build stages, and a checkpoint *writer* to the end of the build stage. When a chunk is emitted from the build stage, after having been successfully handled by both the graph construction *and* vector indexing handlers, its id will be written to a save point in the graph index `extraction_dir`. If a chunk with the same id is subsequently introduced into either the extract or build stage, it will be filtered out by the checkpoint filter.

The following example passes a checkpoint to the `extract_and_build()` method:

```
from graphrag_toolkit.indexing.build import Checkpoint

checkpoint = Checkpoint('my-checkpoint')

...

graph_index.extract_and_build(docs, checkpoint=checkpoint)
```

When you create a `Checkpoint`, you must give it a name. A checkpoint filter will only filter out chunks that were checkpointed by a checkpoint writer with the same name. If you use checkpoints when [running separate extract and build processes](#run-the-extract-and-build-stages-separately), ensure the checkpoints have different names. If you use the same name across separate extract and build processes, the build stage will ignore all the chunks created by the extract stage.

Checkpoints do not provide any transactional guarantees. If a chunk is successfully processed by the graph construction handlers, but then fails in a vector indexing handler, it will not make it to the end of the build pipeline, and so will not be checkpointed. If the build stage is restarted, the chunk will be reprocessed by both the graph construction and vector indexing handlers. For stores that support upserts (e.g. Amazon Neptune Database and Amazon Neptune Analytics) this is not an issue.

The graphrag-toolkit does not clean up checkpoints. If you use checkpoints, periodically clean the checkpoint directory of old checkpoint files. 

### Advanced graph construction

If you want more control over the extract and build stages, then instead of using a `LexicalGraphIndex`, you can use the extract and build pipelines directly: 

```
import os

from graphrag_toolkit.storage import GraphStoreFactory
from graphrag_toolkit.storage import VectorStoreFactory
from graphrag_toolkit.indexing import sink
from graphrag_toolkit.indexing import PROPOSITIONS_KEY
from graphrag_toolkit.indexing.extract import LLMPropositionExtractor
from graphrag_toolkit.indexing.extract import TopicExtractor
from graphrag_toolkit.indexing.extract import GraphScopedValueStore
from graphrag_toolkit.indexing.extract import ScopedValueProvider, DEFAULT_SCOPE
from graphrag_toolkit.indexing.extract import ExtractionPipeline
from graphrag_toolkit.indexing.extract.constants import DEFAULT_ENTITY_CLASSIFICATIONS
from graphrag_toolkit.indexing.build import Checkpoint
from graphrag_toolkit.indexing.build import BuildPipeline
from graphrag_toolkit.indexing.build import VectorIndexing
from graphrag_toolkit.indexing.build import GraphConstruction

from llama_index.core.node_parser import SentenceSplitter
from llama_index.readers.web import SimpleWebPageReader

import nest_asyncio
nest_asyncio.apply()

checkpoint = Checkpoint('advanced-construction-example', enabled=True)

# Create graph and vector stores
graph_store = GraphStoreFactory.for_graph_store(os.environ['GRAPH_STORE'])
vector_store = VectorStoreFactory.for_vector_store(os.environ['VECTOR_STORE'])

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
    initial_scoped_values = { DEFAULT_SCOPE: DEFAULT_ENTITY_CLASSIFICATIONS }
)

topic_extractor = TopicExtractor(
    source_metadata_field=PROPOSITIONS_KEY, # Omit this line if not performing proposition extraction
    entity_classification_provider=entity_classification_provider # Entity classifications saved to graph between LLM invocations
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
    batch_size=25,
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
    metadata_fn=lambda url:{'url': url}
).load_data(doc_urls)

# Run the build and exraction stages
docs | extraction_pipeline | build_pipeline | sink  
```