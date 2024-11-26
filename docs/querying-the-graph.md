[[Home](./)]

## Querying the Graph

For the graphrag-toolkit, the primary unit of context presented to the LLM is the *statement*, which is a standalone assertion or proposition. Source documents are broken into chunks, and from these chunks are extracted statements. In the graphrag-toolkit's [graph model](./graph-model.md), statements are thematically grouped by topic, and supported by facts. At question-answering time, the graphrag-toolkit retrieves groups of statements, and presents them in the context window to the LLM.

The graphrag-toolkit contains two different retrievers: a `TraversalBasedRetriever`, and a `SemanticGuidedRetriever`. The `TraversalBasedRetriever` uses a combination of 'top down' search – finding chunks through vector similarity search, and then traversing from these chunks through topics to statements and facts – and 'bottom up' search, which performs keyword-based lookups of entities, and proceeds through facts to statements and topics. The `SemanticGuidedRetriever` integrates vector-based semantic search with structured graph traversal. It uses semantic and keyword-based searches to identify entry points, then intelligently explores the graph through beam search and path analysis, while employing reranking and diversity filtering to ensure quality results. This hybrid approach enables both precise matching and contextual exploration.

The `SemanticGuidedRetriever` uses a *statement* vector index, whereas the `TraversalBasedRetriever` uses a *chunk* vector index. The chunk vector index is much smaller than the statement index.

In the current release the output formats of the two retrievers are different. Future releases of the graphrag-toolkit will seek to align the outputs.

### TraversalBasedRetriever

The following example uses a `TraversalBasedRetriever` with all its default settings to query the graph:
```
from graphrag_toolkit import LexicalGraphQueryEngine
from graphrag_toolkit.storage import GraphStoreFactory
from graphrag_toolkit.storage import VectorStoreFactory

import nest_asyncio
nest_asyncio.apply()

graph_store = GraphStoreFactory.for_graph_store(
    'neptune-db://my-graph.cluster-abcdefghijkl.us-east-1.neptune.amazonaws.com'
)

vector_store = VectorStoreFactory.for_vector_store(
    'aoss://https://abcdefghijkl.us-east-1.aoss.amazonaws.com'
)

query_engine = LexicalGraphQueryEngine.for_traversal_based_search(
    graph_store, 
    vector_store
)

response = query_engine.query("What are the differences between Neptune Database and Neptune Analytics?")

print(response.response)
```

By default, the `TraversalBasedRetriever` uses a composite search strategy using two subretrievers:

  - `EntityBasedSearch` – This retriever extracts keywords from the query and then looks up entities in the graph based on these keywords. From the entities, the retriever traverses facts, statements and topics. Entity-based search tends to return a broadly-scoped set of results, based on the neighbourhoods of individual entities and the facts that connect entities.
  - `ChunkBasedSearch` – This retriever finds chunks using vector similarity search. From the chunks, the retriever traverses topics, statements, and facts. Chunk-based search tends to return a narrowly-scoped set of results based on the statement and fact neighbourhoods of chunks that match the original query.
  
When combining these two retrievers, the `TraversalBasedRetriever` weights their contributions in favour of the chunk-based search: the chunk search provides a foundation of similarity-based results, which are then augmented by the broader-ranging entity-based results.

To configure the `TraversalBasedRetriever` with one or other of these subetrievers, you can pass an instance of the subretriever, or the type of subretriver, to the factory method:

```
from graphrag_toolkit.retrieval.retrievers import ChunkBasedSearch

...

query_engine = LexicalGraphQueryEngine.for_traversal_based_search(
    graph_store, 
    vector_store,
    retrievers=[ChunkBasedSearch]
)
```

#### TraversalBasedRetriever results

The `TraversalBasedRetriever` uses openCypher queries to explore the graph from entity- and chunk-based start nodes. The retriever returns one or more search results, each of which comprises a source, topic, a set of statements, and a score:

```
{
  "source": "https://docs.aws.amazon.com/neptune/latest/userguide/intro.html",
  "topic": "Amazon Neptune",
  "statements": [
    "Amazon Neptune provides high performance for Resource Description Framework (RDF) model",
    "You can access Resource Description Framework model in Amazon Neptune using SPARQL query language",
    "You can access Property Graph model in Amazon Neptune using openCypher query language",
    "Amazon Neptune provides high performance for Property Graph (PG) model",
    "You can access Property Graph model in Amazon Neptune using Gremlin query language"
  ],
  "score": 0.7
}
{
  "source": "https://docs.aws.amazon.com/neptune-analytics/latest/userguide/neptune-analytics-features.html",
  "topic": "Neptune Analytics and Neptune Database",
  "statements": [
    "Neptune Analytics and Neptune Database are related concepts",
    "Neptune Analytics allows loading graph data from Amazon S3 or a Neptune Database endpoint",
    "Neptune Analytics allows running graph analytics queries using pre-built or custom graph queries",
    "Javascript must be enabled to use the Amazon Web Services Documentation",
    "The document refers to conventions described at /general/latest/gr/docconventions.html"
  ],
  "score": 0.44
}

...

{
  "source": "https://docs.aws.amazon.com/neptune/latest/userguide/intro.html",
  "topic": "Neptune Failover and Replication",
  "statements": [
    "Amazon Neptune supports Gremlin for property graphs",
    "Amazon Neptune provides high performance for property graphs",
    "Amazon Neptune supports open graph APIs for property graphs",
    "Amazon Neptune supports openCypher for property graphs",
    "Amazon Neptune provides high performance for RDF graphs"
  ],
  "score": 0.23
}
```

#### Configuring the TraversalBasedRetriever

You can configure the `TraversalBasedRetriever` by passing named arguments to the `LexicalGraphQueryEngine` factory method, or to the retriever constructor.

| Parameter  | Description | Default Value |
| ------------- | ------------- | ------------- | 
| `max_search_results` | The maximum number of search results to return. A search result comprises one or more statements belonging to the same topic (and source). If set to `None`, all found search results will be returned. | `20` |
| `max_statements_per_topic` | The mazimum number of statements to include with a topic. Limits the size of each search result. If set to `None`, all the statements belonging to the topic that are found as part of the search will be included in the result. | `10` |
| `include_facts` | Determines whether facts, as well as statements, are included in the context returned to the LLM. | `False` |
| `expand_entities` | Used by `EntityBasedSearch` when identifying candidate entities to anchor the traversal. If set to `True`, the retriever considers not only keyword lookup entities, but also additional entities transitively connected to the keyword lookup entities. | `True` |
| `max_keywords` | Used by `EntityBasedSearch` when extracting keywords from the query. When extracting keywords, the retriever attempts to include alternative names, synonyms, abbreviations, and the definitions for any acronyms it recognizes. These all count towards the keyword limit. | `10` |
| `vss_top_k` | Used by `ChunkBasedSearch` when identifying candidate chunks to anchor the traversal. | `10` |
| `vss_diversity_factor` | Used by `ChunkBasedSearch` to identify the most relevant chunks across the broadest range of sources. The retriever does this by looking up `vss_top_k * vss_diversity_factor` chunks, and then iterating through the results looking for the next most relevant result from a previously unseen source until it has satisfied its `vss_top_k` quota. | `5` |
| `derive_subqueries` | Used by `TraversalBasedRetriever`. If set to `True` the retriever will attempt to break complex queries into multiple, simpler queries. Candidates for query decomposition must be longer than 25 characters, and answering the original query must require details of more than one entity. | `False` |
| `max_subqueries` | The maximum number of subqueries into which a complex query will be decomposed. | `2` |
| `reranker` | Prior to returning the results to the query engine for post-processing, the retriever can rerank them based on a reranking of all statements in the results. Valid options here are `tfidf`, `model`, `none`, and the Python `None` keyword. See [Traversal-based reranking](#traversal-based-reranking) below for details. | `tfidf` |
| `max_statements` | Used by the traversal-based reranking strategy. Limits the number of reranked statements across the entire resultset to `max_statements`. If set to `None`, *all* the statements in the resultset will be reranked and returned to the query engine. | `100` |

The example below shows how to configure the `TraversalBasedRetriever` to return ten results:

```
query_engine = LexicalGraphQueryEngine.for_traversal_based_search(
    graph_store, 
    vector_store,
    max_search_results=10
)
```

#### Statement reranking

At the end of the retrieval process, but prior to returning the results to the query engine for post-processing, the `TraversalBasedRetriever` can rerank all the statements in the results. There are two strategies available for doing this. If you set the `reranker` parameter to `model`, the retriever will use LlamaIndex's `SentenceTransformerRerank` to rerank all the statements in the resultset. If you set the `reranker` parameter to `tfidf` (the default), the retriever uses a *term frequency-inverse document frequency* (TF-IDF) measure to rank all the statements in the resultset. `tfidf` tends to be faster than `model`. You can also turn off the reranking feature by setting `reranker` to `none`.

Besides reranking statements, you can also specify the `max_statements` to be returned by the reranker. This will truncate the number of statements subsequently passed to the query engine for post-processsing. `max_statements` is only applied if `reranker` has been set to `model` or `tfidf`.

This traversal-based reranking is performed on a per-statement basis. To facilitate the reranking, each statement is enriched with its topic and source metadata. This composite lexical unit is then reranked against a composite of the original query plus any entity names found in the keyword lookup step. 

You can use the traversal-based reranking *in combination* with any reranking applied during post-processing. Reranking in the post-processing stage will rerank *results* (i.e. collections of statements), whereas traversal-based reranking reranks individual *statements*. 

