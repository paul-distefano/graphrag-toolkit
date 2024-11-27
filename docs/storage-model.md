[[Home](./)]

## Storage Model

### Topics

  - [Overview](#overview)
  - [Graph store](#graph-store)
    - [Neptune Database and Neptune Analytics graph stores](#neptune-database-and-neptune-analytics-graph-stores)
  - [Vector store](#vector-store)
    - [Amazon OpenSearch Serverless and Neptune Analytics vector stores](#amazon-opensearch-serverless-and-neptune-analytics-vector-stores)

### Overview

The graphrag-toolkit uses two separate stores: a `GraphStore` and a `VectorStore`. A `VectorStore` acts as a container for a collection of `VectorIndex`. When constructing or querying a graph, you must provide instances of both a graph store and vector store.

The toolkit provides graph store implementations for both [Amazon Neptune Analytics](https://docs.aws.amazon.com/neptune-analytics/latest/userguide/what-is-neptune-analytics.html) and [Amazon Neptune Database](https://docs.aws.amazon.com/neptune/latest/userguide/intro.html), and vector store implementations for Neptune Analytics and [Amazon OpenSearch Serverless](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html). The graphrag-toolkit provides several convenient factory methods for creating instances of these stores. These factory methods accept connection string-like store identifiers, described below.

> This early release of the toolkit provides support for Amazon Neptune and Amazon OpenSearch Serverless, but we welcome alternative store implementations. The store APIs and the ways in which the stores are used have been designed to anticipate alternative implementations. However, the proof is in the development: if you experience issues developing an alternative store, [let us know](https://github.com/awslabs/graphrag-toolkit/issues).

Graph stores and vector stores provide connectivity to an *existing* storage instance, which you will need to have provisioned beforehand.

### Graph store

Graph stores must support the [openCypher](https://opencypher.org/) property graph query language. Graph construction queries typically use an `UNWIND ... MERGE` idiom to create or update the graph for a [batch of inputs](https://docs.aws.amazon.com/neptune-analytics/latest/userguide/best-practices-content.html#best-practices-content-14). The Neptune graph store implementations override the `GraphStore.node_id()` method to ensure that node ids in the code (e.g. `chunkId`) are mapped to Neptune's `~id` reserved property. Alternative graph store implementations can leave the base implementation of `node_id()` as-is. This will result in node ids being mapped to a property of the same name (i.e. a reference to `chunkId` in the code will be mapped to a `chunkId` property of a node).

#### Neptune Database and Neptune Analytics graph stores

You can use the `GraphStoreFactory.for_graph_store()` static factory method to create an instance of a Neptune Analytics or Neptune Database graph store.

To create a Neptune Database graph store, supply a connection string that begins `neptune-db://`, followed by an [endpoint](https://docs.aws.amazon.com/neptune/latest/userguide/feature-overview-endpoints.html):

```
from graphrag_toolkit.storage import GraphStoreFactory

neptune_connection_info = 'neptune-db://mydbcluster.cluster-123456789012.us-east-1.neptune.amazonaws.com:8182'

graph_store = GraphStoreFactory.for_graph_store(neptune_connection_info)
```

To create a Neptune Analytics graph store, supply a connection string that begins `neptune-graph://`, followed by the graph's identifier:

```
from graphrag_toolkit.storage import GraphStoreFactory

neptune_connection_info = 'neptune-graph://g-jbzzaqb209'

graph_store = GraphStoreFactory.for_graph_store(neptune_connection_info)
```

### Vector store

A vector store is a collection of vector indexes. The graphrag-toolkit uses up to two vector indexes: a chunk index and a statement index. The chunk index is typically much smaller than the statement index. If you want to use the vector-guided retriever, you will need to enable the statement index. If you want to use the traversal-based retriever, you will need to enable the chunk index. If you want to use both retrievers, you will need to enable both indexes. (The `VectorStoreFactory` described below enables both indexes by default.)

#### Amazon OpenSearch Serverless and Neptune Analytics vector stores

You can use the `VectorStoreFactory.for_vector_store()` static factory method to create an instance of an Amazon OpenSearch Serverless or Neptune Database vector store.

To create an Amazon OpenSearch Serverless vector store, supply a connection string that begins `aoss://`, followed the https endpoint of the OpenSearch Serverless collection:

```
from graphrag_toolkit.storage import VectorStoreFactory

opensearch_connection_info = 'aoss://https://123456789012.us-east-1.aoss.amazonaws.com'

vector_store = VectorStoreFactory.for_vector_store(opensearch_connection_info)
```

To create a Neptune Analytics vector store, supply a connection string that begins `neptune-graph://`, followed by the graph's identifier:

```
from graphrag_toolkit.storage import VectorStoreFactory

neptune_connection_info = 'neptune-graph://g-jbzzaqb209'

vector_store = VectorStoreFactory.for_vector_store(neptune_connection_info)
```

By default, the `VectorStoreFactory` will enable both the statement index and the chunk index. If you want to enable just one of the indexes, pass an `index_names` argument to the factory method:

```
vector_store = VectorStoreFactory.for_vector_store(opensearch_connection_info, index_names=['chunk'])
```

