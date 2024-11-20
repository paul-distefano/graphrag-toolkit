[[Home](./)]

## Configuration

| Parameter  | Description | Default Value |
| ------------- | ------------- | ------------- |
| `extraction_llm` | LLM used to perform graph extraction | `anthropic.claude-3-sonnet-20240229-v1:0` |
| `response_llm` | LLM used to generate responses | `anthropic.claude-3-sonnet-20240229-v1:0` |
| `embed_model` | Embedding model used to generate embeddings for indexed data and queries | `cohere.embed-english-v3` |
| `embed_dimensions` | Number of dimensions in each vector | `1024` |
| `extraction_pipeline_num_workers` | The number of parallel processes to use when running the extract stage | `2` |
| `extraction_pipeline_batch_size` | The number of input nodes to be processed in parallel by *all workers* in the extract stage | `4` |
| `build_pipeline_num_workers` | The number of parallel processes to use when running the build stage | `2` |
| `build_pipeline_batch_size` | The number of input nodes to be processed in parallel by *each worker* in the build stage | `25` |
| `build_pipeline_batch_writes_enabled` | Determines whether, on a per-worker basis, to write all elements (nodes and edges, or vectors) emitted by a batch of input nodes as a bulk operation, or singly to the graph and vector stores| `True` |
| `enable_cache` | Determines whether the results of LLM calls to models on Amazon Bedrock are cached to the local filesystem | `False` |

#### LLM configuration

The `extraction_llm` and `response_llm` configuration parameters accept three different types of value:

  - You can pass an instance of a LlamaIndex `LLM` object. This allows you to configure the graphrag-toolkit for LLM backends other than Amazon bedrock.
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

  - You can pass an instance of a LlamaIndex `BaseEmbedding` object. This allows you to configure the graphrag-toolkit for embedding backends other than Amazon bedrock.
  - You can pass the model name of an Amazon Bedrock model. For example: `amazon.titan-embed-text-v1`.
  - You can pass a JSON string representation of a LlamaIndex `Bedrock` instance. For example:
  
  ```
  {
    "model_name": "amazon.titan-embed-text-v2:0",
    "dimensions": 512
  }
  ```
  
When configuring an embedding model, you must also set the `embed_dimensions` configuration parameter.