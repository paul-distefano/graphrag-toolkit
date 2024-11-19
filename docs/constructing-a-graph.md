[[Home](./)]

## Constructing a Graph

There are two stages to graph construction: extract, and build. The graphrag-toolkit uses separate pipelines for each of these stages, plus micro-batching, to provide a continous ingest capability. This means that your graph will start being populated soon after extraction begins.

You can run the extract and build pipelines together, to provide for the continuous ingest described above. Or you can run the two pipelines separately, extracting first to file-based chunks, and then later building a graph from these chunks.

The `LexicalGraphIndex` is a convenience class that allows you to run the extract and build pipelines together or separately. Alternatively, you can build your graph construction application using the underlying pipelines. This gives you more control over the configuration of each stage. We describe these two different approaches in the [Using the LexicalGraphIndex to construct a graph](#using-the-lexicalgraphindex-to-construct-a-graph) and [Advanced graph construction](#advanced-graph-construction) sections below.

#### Extract

The extraction stage is, by default, a three-step process: 

  1. The source documents are broken down into chunks.
  2. For each chunk, an LLM extracts a set of propositions from the unstructured content. This proposition extraction helps 'clean' the content and improve the subsequent entity/topic/statement/fact extraction by breaking complex sentences into simpler sentences, replacing pronouns with specific names, and replacing acronyms where possible. These propositions are added to the chunk's metadata under the `aws::graph::propositions` key.
  3. Following the proposition extraction, a second LLM call extracts entities, relations, topics, statements and facts from the set of extracted propositions. These details are added to the chunk's metadata under the `aws::graph::topics` key.
  
Only the third step here is mandatory. If your source data has already been chunked (you're importing from an Amazon Bedrock Knowledge Base, for example), you can omit step 1. If you're willing to trade a reduction in LLM calls and improved performance for a reduction in the quality of the entity/topic/statement/fact extraction, you can omit step 2.

#### Build

In the build stage, the LlamaIndex chunk nodes emitted from the extract stage are broken down further into a stream of individual source, chunk, topic, statement and fact LlamaIndex nodes. Graph construction and vector indexing handlers process these nodes to build and index the graph content. Each of these nodes has an `aws::graph::index` metadata item containing data that can be used to index the node in a vector store (though only the chunk and statement nodes are actually indexed in the current implementation).

### Using the LexicalGraphIndex to construct a graph

The `LexicalGraphIndex` provides a convenient means of constructing a graph – via either continuous ingest, or separate extract and build stages. When constructing a `LexicalGraphIndex` you must supply a graph store and a vector store (see [Storage Model](./storage-model.md) for more details). In the examples below, the graph store and vector store connection information is fetched from environment variables.

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

#### Run separate extract and build steps

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

#### Configuring the extract and build steps

You can configure the `LexicalGraphIndex` extract and build stages in two different respects. You can configure the number of workers and batch sizes for each strage using the `GraphRAGConfig` object. See [Configuration]('./configuration.md') for more details on using the configuration object, and the [Architecture]('./architecture.md') section on the implications of varying the number of workers and batch sizes in each of the stages. Besides configuring the workers and batch sizes, you can also configure the extraction process with regard to chunking, proposition extraction and entity classification.
  

### Advanced graph construction

ConflictException
ConcurrentModificationException