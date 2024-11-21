[[Home](./)]

## Querying the Graph

For the graphrag-toolkit, the primary unit of context presented to the LLM is the *statement*, which is a standalone assertion or proposition. Source documents are broken into chunks, and from these chunks are extracted statements. In the [graph model](./graph-model.md), statements are thematically grouped by topic, and supported by facts. At question-answering time, the graphrag-toolkit retrieves groups of statements, and presents them in the context window to the LLM.

The graphrag-toolkit contains two different retrievers: a `TraversalBasedRetriever`, and a `VectorGuidedRetriever`. The `TraversalBasedRetriever` uses a combination of 'top down' search – finding chunks through vector similarity search, and then traversing from these chunks through topics to statements and facts – and 'bottom up' search, which performs keyword-based lookups of entities, and proceeds through facts to statements and topics. The `VectorGuidedRetriever`... TODO

### TraversalBasedRetriever

| Parameter  | Description | Default Value |
| ------------- | ------------- | ------------- | 
| `expand_entities` | Used by `EntityBasedSearch` when identifying entities to anchor the traversal. If set to `True`, the retriever considers additional entities transitively connected to the keyword lookup entities. | `True` |
| `include_facts` | Determines whether facts, as well as statements, are included in the context returned to the LLM. | `False` |
| `max_search_results` | The maximum number of search results to return. A search result comprises one or more statements belonging to the same topic (and source). | `20` |

expand_entities True
include_facts False


max_statements 100
max_search_results 20
max_statements_per_topic 10
max_keywords 5
derive_subqueries False
max_subqueries 2
vss_top_k 10
vss_diversity_factor 5
reranker tfidf
format_source_metadata_fn