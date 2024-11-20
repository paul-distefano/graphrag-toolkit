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
| `build_pipeline_num_workers` | The number of parallel processes to use when running the build state | `2` |
| `build_pipeline_batch_size` | The number of input nodes to be processed in parallel by *each worker* in the build stage | `25` |
| `build_pipeline_batch_writes_enabled` | Determines whether, on a per-worker basis, to write all elements (nodes and edges, or vectors) emitted by a batch of input nodes as a bulk operation, or singly| `True` |
| `enable_cache` | Determines whether the results of LLM calls to models on Amazon Bedrock are cached to the local filesystem | `False` |

