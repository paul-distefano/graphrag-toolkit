[[Home](./)]

## Querying the Graph

For the graphrag-toolkit, the primary unit of context presented to the LLM is the *statement*, which is a standalone assertion or proposition. Source documents are broken into chunks, and from these chunks are extracted statements. In the graphrag-toolkit's [graph model](./graph-model.md), statements are thematically grouped by topic, and supported by facts. At question-answering time, the graphrag-toolkit retrieves groups of statements, and presents them in the context window to the LLM.

The graphrag-toolkit contains two different retrievers: a `TraversalBasedRetriever`, and a `VectorGuidedRetriever`. The `TraversalBasedRetriever` uses a combination of 'top down' search – finding chunks through vector similarity search, and then traversing from these chunks through topics to statements and facts – and 'bottom up' search, which performs keyword-based lookups of entities, and proceeds through facts to statements and topics. The `VectorGuidedRetriever`... TODO

### TraversalBasedRetriever

```
{
  "source": "https://docs.aws.amazon.com/neptune/latest/userguide/intro.html",
  "topics": [
    {
      "topic": "Amazon Neptune",
      "statements": [
        "You can access Resource Description Framework model in Amazon Neptune using SPARQL query language",
        "Amazon Neptune provides high performance for Resource Description Framework (RDF) model",
        "You can access Property Graph model in Amazon Neptune using openCypher query language",
        "Amazon Neptune provides high performance for Property Graph (PG) model",
        "You can access Property Graph model in Amazon Neptune using Gremlin query language"
      ]
    }
  ],
  "score": 0.71
}
{
  "source": "https://docs.aws.amazon.com/neptune-analytics/latest/userguide/neptune-analytics-features.html",
  "topics": [
    {
      "topic": "Neptune Analytics and Neptune Database",
      "statements": [
        "Neptune Analytics and Neptune Database are related concepts",
        "Neptune Analytics allows loading graph data from Amazon S3 or a Neptune Database endpoint",
        "Neptune Analytics allows running graph analytics queries using pre-built or custom graph queries",
        "Javascript must be enabled to use the Amazon Web Services Documentation",
        "The document refers to conventions described at /general/latest/gr/docconventions.html"
      ]
    }
  ],
  "score": 0.44
}

...

{
  "source": "https://docs.aws.amazon.com/neptune/latest/userguide/intro.html",
  "topics": [
    {
      "topic": "Neptune Failover and Replication",
      "statements": [
        "Amazon Neptune supports Gremlin for property graphs",
        "Amazon Neptune provides high performance for property graphs",
        "Amazon Neptune supports open graph APIs for property graphs",
        "Amazon Neptune supports openCypher for property graphs",
        "Amazon Neptune supports open graph APIs for RDF graphs"
      ]
    }
  ],
  "score": 0.24
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
