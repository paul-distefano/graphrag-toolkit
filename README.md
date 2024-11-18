## GraphRAG Toolkit

The graphrag-toolkit is a Python toolkit for building GraphRAG applications. It provides a framework for automating the construction of a graph from unstructured data, and composing question-answering strategies that target this graph. 

The toolkit uses low-level [LlamaIndex](https://docs.llamaindex.ai/en/stable/)  components – data connectors, metadata extractors, and transforms – to implement much of the graph construction process. By default, the toolkit uses [Amazon Neptune Analytics](https://docs.aws.amazon.com/neptune-analytics/latest/userguide/what-is-neptune-analytics.html) or [Amazon Neptune Database](https://docs.aws.amazon.com/neptune/latest/userguide/intro.html) for its graph store, and Neptune Analytics or [Amazon OpenSearch Serverless](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html) for its vector store, but it also provides extensibility points for adding alternative graph stores and vector stores. The default backend for LLMs and embedding models is [Amazon Bedrock](https://docs.aws.amazon.com/bedrock/); but, as with the stores, the toolkit can be configured for other LLM and embedding model backends using LlamaIndex abstractions.

## Installation

The graphrag-toolkit requires python and [pip](http://www.pip-installer.org/en/latest/) to install. You can install the graphrag-toolkit using pip:

```
$ pip install https://github.com/awslabs/graphrag-toolkit/releases/latest/download/graphrag-toolkit.zip
```

### Supported Python versions

The graphrag-toolkit requires Python 3.10 or greater.

## Example of use

### Constructing a graph

```
from graphrag_toolkit import LexicalGraphIndex
from graphrag_toolkit.storage import GraphStoreFactory
from graphrag_toolkit.storage import VectorStoreFactory

from llama_index.readers.web import SimpleWebPageReader

import nest_asyncio
nest_asyncio.apply()

doc_urls = [
    'https://aws.amazon.com/about-aws/whats-new/2024/04/amazon-timestream-liveanalytics-fedramp-high-authorization-aws-govcloud-west-region/',
    'https://aws.amazon.com/about-aws/whats-new/2024/03/amazon-timestream-influxdb-available/'
]

docs = SimpleWebPageReader(html_to_text=True).load_data(doc_urls)

graph_store = GraphStoreFactory.for_graph_store(
    'neptune-db://my-graph.cluster-abcdefghijkl.us-east-1.neptune.amazonaws.com'
)

vector_store = VectorStoreFactory.for_vector_store(
    'aoss://https://abcdefghijkl.us-east-1.aoss.amazonaws.com'
)

graph_index = LexicalGraphIndex(
    graph_store, 
    vector_store
)

graph_index.extract_and_build(docs)
```

### Querying the graph

```
from graphrag_toolkit import LexicalGraphQueryEngine
from graphrag_toolkit.storage import GraphStoreFactory
from graphrag_toolkit.storage import VectorStoreFactory

import nest_asyncio
nest_asyncio.apply()

graph_store = GraphStoreFactory.for_graph_store(
    'neptune-db://my-graph.cluster-abcdefghijkl.us-east-1.neptune.amazonaws.com'
)

vector_store = VectorStoreFactory.for_vector_store(
    'aoss://https://abcdefghijkl.us-east-1.aoss.amazonaws.com'
)

query_engine = LexicalGraphQueryEngine.for_traversal_based_search(
    graph_store, 
    vector_store
)

response = query_engine.query("When was Timestream for InfluxDB released?")

print(response.response)
```

## Documentation

  - [Constructing a graph](./docs/constructing-a-graph.md) 
  - [Querying the graph](./docs/querying-the-graph.md) 
  - [Configuration](./docs/configuration.md) 
  - [Architecture](./docs/architecture.md)
  - [Graph model](./docs/graph-model.md)


### Supported Python versions

The graphrag-toolkit requires Python 3.10 or greater.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

