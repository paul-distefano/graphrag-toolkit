[[Home](./)]

## Storage Model

The graphrag-toolkit uses two separate stores: a `GraphStore` and a `VectorStore`. A `VectorStore` acts as a container for a collection of `VectorIndex`. When constructing or querying a graph, you must provide instances of both a graph store and vector store.

The toolkit provides graph store implementations for both [Amazon Neptune Analytics](https://docs.aws.amazon.com/neptune-analytics/latest/userguide/what-is-neptune-analytics.html) and [Amazon Neptune Database](https://docs.aws.amazon.com/neptune/latest/userguide/intro.html), and vector store implementations for Neptune Analytics and [Amazon OpenSearch Serverless](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html).

> This early release of the toolkit provides support for Amazon Neptune and Amazon OpenSearch Serverless, but we welcome alternative store implementations. The store APIs and the ways in which the stores are used have been designed to anticipate alternative implementations. However, the proof is in the development: if you experience issues developing an alternative store, [let us know](https://github.com/awslabs/graphrag-toolkit/issues).

THe graphrag-toolkit provides several convenient factory methods for creating store instances. These factory methods accept connection string-like store identifiers, described below.

