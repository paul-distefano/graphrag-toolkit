[[Home](./)]

## Querying the Graph

The graphrag-toolkit uses a lexical graph to supply a question-answering LLM with pieces of text extracted from the corpus. When using a lexical graph in a RAG application in this way, the question arises: what size lexical unit should form the basis of the context?

For many RAG applications, the primary unit of context is the *chunk*: that is, the context window is formed of one or more chunks retrieved from the corpus. Different chunking startegies produce different sized chunks: there's no one-size-fits-all definition of a chunk. For the purpose of this documentation, however, we take a chunk to be something larger than an individual sentence, smaller than an entire document.

For the graphrag-toolkit, the primary unit of context is not the chunk, but the *statement*, which is a standalone assertion or proposition. Source documents are broken into chunks, and from these chunks are extracted statements. In the [graph model](./graph-model.md), statements are thematically grouped by topic, and supported by facts. At question-answering time, the graphrag-toolkit retrieves groups of statements, and presents them in the context window to the LLM.

Graphs can help question-answering systems retrieve information which is *semantically dissimilar from the question*, but nonetheless *relevant to the answer*. Retrieval through semantic similarity remains an important strategy, and context that is semantically similar to the question will often comprise the foundation of a good answer. But that's not always the case, and in many circumstances it will also be necessary to find and return information that cannot be found by vector similarity search alone, in order to present the LLM with a more differentiated context that can help it develop comparisons, arguments, and summaries.

The graphrag-toolkit contains two different retrievers: a `TraversalBasedRetriever`, and a `VectorGuidedRetriever`. The `TraversalBasedRetriever` uses a combination of 'top down' search – finding chunks through vector similarity search, and then traversing from these chunks through topics to statements and facts – and 'bottom up' search, which performs keyword-based lookups of entities, and proceeds through facts to statements and topics. The `VectorGuidedRetriever`... TODO