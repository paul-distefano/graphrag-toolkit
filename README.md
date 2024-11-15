## GraphRAG Toolkit

graphrag-toolkit is a Python toolkit for building GraphRAG applications. It provides a framework for automating the construction of a graph from unstructured data, and composing question-answering strategies that target this graph. 

The toolkit uses low-level [LlamaIndex](https://docs.llamaindex.ai/en/stable/)  components – data connectors, metadata extractors, and transforms – to implement much of the graph construction process. By default, the toolkit uses [Amazon Neptune Analytics](https://docs.aws.amazon.com/neptune-analytics/latest/userguide/what-is-neptune-analytics.html) or [Amazon Neptune Database](https://docs.aws.amazon.com/neptune/latest/userguide/intro.html) for its graph store, and Neptune Analytics or [Amazon OpenSearch Serverless](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html) for its vector store. However, it also provides extensibility points for adding new graph stores and vector stores. Likewise, the default backend for LLMs and embedding models is [Amazon Bedrock](https://docs.aws.amazon.com/bedrock/); but, as with the stores, the toolkit can be configured for other LLM and embedding model backends using LlamaIndex abstractions.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

