[[Home](./)]

## Querying the Graph

For the graphrag-toolkit, the primary unit of context presented to the LLM is the *statement*, which is a standalone assertion or proposition. Source documents are broken into chunks, and from these chunks are extracted statements. In the graphrag-toolkit's [graph model](./graph-model.md), statements are thematically grouped by topic, and supported by facts. At question-answering time, the graphrag-toolkit retrieves groups of statements, and presents them in the context window to the LLM.

The graphrag-toolkit contains two different retrievers: a `TraversalBasedRetriever`, and a `VectorGuidedRetriever`. The `TraversalBasedRetriever` uses a combination of 'top down' search – finding chunks through vector similarity search, and then traversing from these chunks through topics to statements and facts – and 'bottom up' search, which performs keyword-based lookups of entities, and proceeds through facts to statements and topics. The `VectorGuidedRetriever`... TODO

### TraversalBasedRetriever

```
{
  "source": "https://docs.aws.amazon.com/neptune-analytics/latest/userguide/neptune-analytics-vs-neptune-database.html",
  "topics": [
    {
      "topic": "Neptune Analytics",
      "statements": [
        "Processing thousands of analytic queries per second using popular graph analytics algorithms becomes possible with Neptune Analytics",
        "Neptune Analytics uses popular graph analytic algorithms",
        "You can use Neptune Analytics to analyze and query graphs in data science workflows that build targeted content recommendations",
        "Neptune Analytics uses low-latency analytic queries",
        "Neptune Analytics makes it easy to apply powerful algorithms to the data in your Neptune Database"
      ]
    }
  ],
  "score": 0.61
}
{
  "source": "https://docs.aws.amazon.com/neptune/latest/userguide/intro.html",
  "topics": [
    {
      "topic": "Neptune and Neptune Analytics",
      "statements": [
        "Neptune Analytics uses popular graph analytic algorithms.",
        "Neptune Analytics uses low-latency analytic queries.",
        "Neptune Analytics complements Neptune database.",
        "Neptune Analytics is an analytics database engine.",
        "Neptune Analytics can find trends in graph data."
      ]
    }
  ],
  "score": 0.56
}
{
  "source": "https://docs.aws.amazon.com/neptune/latest/userguide/intro.html",
  "topics": [
    {
      "topic": "Amazon Neptune",
      "statements": [
        "Amazon Neptune uses popular graph analytic algorithms",
        "Amazon Neptune uses low-latency analytic queries",
        "Neptune powers recommendation engines use case",
        "Before designing a database, consult the GitHub repository \"AWS Reference Architectures for Using Graph Databases\" to inform choices about graph data models and query languages, and browse examples of reference deployment architectures",
        "The Neptune database is highly available"
      ]
    }
  ],
  "score": 0.48
}
```

| Parameter  | Description | Default Value |
| ------------- | ------------- | ------------- | 
| `max_search_results` | The maximum number of search results to return. A search result comprises one or more statements belonging to the same topic (and source). If set to `None`, all found search results will be returned. | `20` |
| `max_statements_per_topic` | The mazimum number of statements to include with a topic. Limits the size of each search result. If set to `None`, all the statements belonging to the topic that are found as part of the search will be included in the result. | `10` |
| `include_facts` | Determines whether facts, as well as statements, are included in the context returned to the LLM. | `False` |
| `expand_entities` | Used by `EntityBasedSearch` when identifying candidate entities to anchor the traversal. If set to `True`, the retriever considers not only keyword lookup entities, but also additional entities transitively connected to the keyword lookup entities. | `True` |
| `max_keywords` | Used by `EntityBasedSearch` when extracting keywords from the query. When extracting keywords, the retriever attempts to include alternative names, synonyms, abbreviations, and the definitions for any acronyms it recognizes. These all count towards the keyword limit. | `10` |
| `vss_top_k` | Used by `ChunkBasedSearch` when identifying candidate chunks to anchor the traversal. | `10` |
| `vss_diversity_factor` | Used by `ChunkBasedSearch` to identify the most relevant chunks across the broadest range of sources. The retriever does this by looking up `vss_top_k * vss_diversity_factor` chunks, and then iterating through the results looking for the next most relevant result from a previously unseen source until it has satisfied its `vss_top_k` quota. | `5` |
| `derive_subqueries` | Used by `TraversalBasedRetriever`. If set to `True` the retriever will attempt to break complex queries into multiple, simpler queries. Candidates for query decomposition must be longer than 25 characters, and answeting the original query must require details of more than one entity. | `False` |
| `max_subqueries` | The maximum number of subqueries into which a complex query will be decomposed. | `2` |
| `reranker` | Prior to returning the results to the query engine for post-processing, the retriever can rerank them based on a reranking of all statements in the results. Valid options here are `tfidf`, `model`, `none`, and the Python `None` keyword. See [Traversal-based reranking](#traversal-based-reranking) below for details. | `tfidf` |
| `max_statements` | Used by the traversal-based reranking strategy. Limits the number of reranked statements across the entire resultset to `max_statements`. If set to `None`, *all* the statements in the resultset will be reranked and returned to the query engine. | `100` |
| `format_source_metadata_fn` | See [Traversal-based reranking](#traversal-based-reranking) below for details. |  See below |
