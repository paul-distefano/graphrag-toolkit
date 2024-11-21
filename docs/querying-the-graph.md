[[Home](./)]

## Querying the Graph

For the graphrag-toolkit, the primary unit of context presented to the LLM is the *statement*, which is a standalone assertion or proposition. Source documents are broken into chunks, and from these chunks are extracted statements. In the [graph model](./graph-model.md), statements are thematically grouped by topic, and supported by facts. At question-answering time, the graphrag-toolkit retrieves groups of statements, and presents them in the context window to the LLM.

The graphrag-toolkit contains two different retrievers: a `TraversalBasedRetriever`, and a `VectorGuidedRetriever`. The `TraversalBasedRetriever` uses a combination of 'top down' search – finding chunks through vector similarity search, and then traversing from these chunks through topics to statements and facts – and 'bottom up' search, which performs keyword-based lookups of entities, and proceeds through facts to statements and topics. The `VectorGuidedRetriever`... TODO

### TraversalBasedRetriever

| Parameter  | Description | Default Value |
| ------------- | ------------- | ------------- | 
| `max_search_results` | The maximum number of search results to return. A search result comprises one or more statements belonging to the same topic (and source). If set to `None`, all found search results will be returned. | `20` |
| `max_statements_per_topic` | The mazimum number of statements to include with a topic. Limits the size of each search result. If set to `None`, all the statements belonging to the topic that are found as part of the search will be included in the result. | `10` |
| `include_facts` | Determines whether facts, as well as statements, are included in the context returned to the LLM. | `False` |

| `expand_entities` | Used by `EntityBasedSearch` when identifying candidate entities to anchor the traversal. If set to `True`, the retriever considers not only keyword lookup entities, but also additional entities transitively connected to the keyword lookup entities. | `True` |
| `max_keywords` | Used by `EntityBasedSearch` when extracting keywords from the query. When extracting keywords, the retriever attempts to include alternative names, synonyms, abbreviations, and the definitions for any acronyms it recognizes. These all count towards the keyword limit. | `10` |
| `vss_top_k` | Used by `ChunkBasedSearch` when identifying candidate chunks to anchor the traversal. | `10` |
| `vss_diversity_factor` | Used by `ChunkBasedSearch` to identify the most relevant chunks across the broadest range of sources. The retriever does this by looking up `vss_top_k * vss_diversity_factor` chunks. and then iterating through the results looking for the next most relevant result from a previously unseen source until it has satisfied its `vss_top_k` quota. | `5` |


derive_subqueries False
max_subqueries 2
reranker tfidf
max_statements 100
format_source_metadata_fn