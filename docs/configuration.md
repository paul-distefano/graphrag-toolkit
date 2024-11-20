[[Home](./)]

## Configuration

The

### GraphRAGConfig

`GraphRAGConfig` allows you to configure LLMs, embedding models, and the extract and build processes. The configuration includes the follwoing parameters:

| Parameter  | Description | Default Value | Environment Variable
| ------------- | ------------- | ------------- | ------------- |
| `extraction_llm` | LLM used to perform graph extraction (see [LLM configuration](#llm-configuration)) | `anthropic.claude-3-sonnet-20240229-v1:0` | `EXTRACTION_MODEL` |
| `response_llm` | LLM used to generate responses (see [LLM configuration](#llm-configuration)) | `anthropic.claude-3-sonnet-20240229-v1:0` | `            self.response_llm = os.environ.get('RESPONSE_MODEL', DEFAULT_RESPONSE_MODEL)
` |
| `embed_model` | Embedding model used to generate embeddings for indexed data and queries (see [Embedding model configuration](#embedding-model-configuration)) | `EMBEDDINGS_MODEL` | `cohere.embed-english-v3` |
| `embed_dimensions` | Number of dimensions in each vector | `1024` | `EMBEDDINGS_DIMENSIONS` |
| `extraction_pipeline_num_workers` | The number of parallel processes to use when running the extract stage | `2` | `EXTRACTION_PIPELINE_NUM_WORKERS` |
| `extraction_pipeline_batch_size` | The number of input nodes to be processed in parallel by *all workers* in the extract stage | `4` | `EXTRACTION_PIPELINE_BATCH_SIZE` |
| `build_pipeline_num_workers` | The number of parallel processes to use when running the build stage | `2` | `BUILD_PIPELINE_NUM_WORKERS` |
| `build_pipeline_batch_size` | The number of input nodes to be processed in parallel by *each worker* in the build stage | `25` | `BUILD_PIPELINE_BATCH_SIZE` |
| `build_pipeline_batch_writes_enabled` | Determines whether, on a per-worker basis, to write all elements (nodes and edges, or vectors) emitted by a batch of input nodes as a bulk operation, or singly to the graph and vector stores (see [Batch writes](#batch-writes)) | `True` | `BUILD_PIPELINE_BATCH_WRITES_ENABLED` |
| `enable_cache` | Determines whether the results of LLM calls to models on Amazon Bedrock are cached to the local filesystem (see [Caching Amazon Bedrock LLM responses](#caching-amazon-bedrock-llm-responses)) | `False` | `ENABLE_CACHE` |

To set a configuration parameter:

```
from graphrag_toolkit import GraphRAGConfig

GraphRAGConfig.response_llm = 'anthropic.claude-3-haiku-20240307-v1:0' 
GraphRAGConfig.extraction_pipeline_num_workers = 4
```

#### LLM configuration

The `extraction_llm` and `response_llm` configuration parameters accept three different types of value:

  - You can pass an instance of a LlamaIndex `LLM` object. This allows you to configure the graphrag-toolkit for LLM backends other than Amazon Bedrock.
  - You can pass the model id of an Amazon Bedrock model. For example: `anthropic.claude-3-haiku-20240307-v1:0`.
  - You can pass a JSON string representation of a LlamaIndex `Bedrock` instance. For example:
  
  ```
  {
    "model": "anthropic.claude-3-sonnet-20240229-v1:0",
    "temperature": 0.0,
    "max_tokens": 4096,
    "streaming": true
  }
  ```
  
#### Embedding model configuration

The `embed_model` configuration parameter accepts three different types of value:

  - You can pass an instance of a LlamaIndex `BaseEmbedding` object. This allows you to configure the graphrag-toolkit for embedding backends other than Amazon Bedrock.
  - You can pass the model name of an Amazon Bedrock model. For example: `amazon.titan-embed-text-v1`.
  - You can pass a JSON string representation of a LlamaIndex `Bedrock` instance. For example:
  
  ```
  {
    "model_name": "amazon.titan-embed-text-v2:0",
    "dimensions": 512
  }
  ```
  
When configuring an embedding model, you must also set the `embed_dimensions` configuration parameter.

#### Batch writes

The graphrag-toolkit use microbatching to progress source data through the extract and build stages.

  - In the extract stage a batch of source nodes is processed in parallel by one or more workers, with each worker performing chunking, proposition extraction and topic/statement/fact/entity extraction over its allocated source nodes. For a given batch of source nodes, the extract stage emits a batch of chunks derived from those source nodes.
  - In the build stage, a batch of chunks from the extract stage are broken down into smaller *indexable* nodes representing sources, chunks, topics, statements and facts. These indexable nodes are then processed by graph construction and vector indexing handlers.

The `build_pipeline_batch_writes_enabled` configuration parameter determines whether all of the indexable nodes derived from a batch of incoming chunks are written to the graph and vector stores singly, or as a bulk operation. Bulk/batch operations tend to improve the throughput of the build stage, at the expense of some additonal latency with regard to this data becoming available to query.

#### Caching Amazon Bedrock LLM responses

If you're using Amazon Bedrock, you can use the local filesystem to cache and reuse LLM responses. Set `enable_cache` to `True`. LLM responses will then be saved in clear text to a `cache` directory. Subsequent invocations of the same model with the exact same prompt will return the cached response.

The `cache` directory can grow very large, particularly if you are caching extarction responses for a very large ingest. The graphrag-toolkit will not manage the size of this directory or delete old entries. If you enable the cache, ensure you clear or prune th ecache directory regularly.