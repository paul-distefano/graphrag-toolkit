## GraphRAG Toolkit

The graphrag-toolkit is a Python toolkit for building GraphRAG applications. It provides a framework for automating the construction of a graph from unstructured data, and composing question-answering strategies that target this graph. 

The toolkit uses low-level [LlamaIndex](https://docs.llamaindex.ai/en/stable/)  components – data connectors, metadata extractors, and transforms – to implement much of the graph construction process. By default, the toolkit uses [Amazon Neptune Analytics](https://docs.aws.amazon.com/neptune-analytics/latest/userguide/what-is-neptune-analytics.html) or [Amazon Neptune Database](https://docs.aws.amazon.com/neptune/latest/userguide/intro.html) for its graph store, and Neptune Analytics or [Amazon OpenSearch Serverless](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html) for its vector store, but it also provides extensibility points for adding alternative graph stores and vector stores. The default backend for LLMs and embedding models is [Amazon Bedrock](https://docs.aws.amazon.com/bedrock/); but, as with the stores, the toolkit can be configured for other LLM and embedding model backends using LlamaIndex abstractions.

## Installation

The graphrag-toolkit requires python and [pip](http://www.pip-installer.org/en/latest/) to install. You can install the graphrag-toolkit using pip:

```
$ pip install https://github.com/awslabs/graphrag-toolkit/releases/latest/download/graphrag-toolkit.zip
```

### Supported Python versions

The graphrag-toolkit requires Python 3.10 or greater

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

