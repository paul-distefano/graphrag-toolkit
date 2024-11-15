## GraphRAG Toolkit

graphrag-toolkit is a Python toolkit for building GraphRAG applications. It provides a framework for automating the construction of a graph from unstructured data, and composing question-answering strategies that target this graph. 

The toolkit uses low-level [LlamaIndex components](https://docs.llamaindex.ai/en/stable/) – data connectors, metadata extractors, and transforms – to implement much of the graph construction process. By default, the toolkit uses Amazon Neptune Analytics or Neptune Database for its graph store, and Neptune Analytics or Amazon OpenSearch Serverless for its vector store. However, it also provides extensibility points for adding new graph stores and vector stores. Likewise, the default backend for LLMs and embedding models is Amazon Bedrock; but, as with the stores, the toolkit can be configured for other LLM and embedding model backends using LlamaIndex abstractions.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

