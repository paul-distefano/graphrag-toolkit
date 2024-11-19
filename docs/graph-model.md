## Graph Model

The graphrag-toolkit uses a form of hierarchical [lexical graph](https://graphr.ag/reference/knowledge-graph/lexical-graph-hierarchical-structure/), auto-generated from unstructured sources, whose job is to help question-answering systems retrieve information which is *semantically dissimilar from the question*, but nonetheless *relevant to the answer*.

The graph has three tiers:

  - **Lineage** Sources, chunks, and the relations between them.
  - **Summarisation** Hierarchical summarisations and semantic units at different levels of granularity.
  - **Entity-Relationship** Individual entities and relations extracted from the underlying sources.
  
### Lineage tier

This tier consists of `Source` nodes and `Chunk` nodes. A source node contains metadata describing a source document (e.g. author, URL, publication date). The exact metadata varies depending on the source. Chunks contain the actual chunked text (and its embedding). Chunks are linked to previous, next, parent and child chunks.

### Entity-Relationship tier

This consists of `Entity` nodes and `RELATION` relationships. Entities have a value (e.g. 'Amazon') and a classification (e.g. 'Company'). Relationships have a value (e.g. 'WORKS_FOR').

The entities in the entity-relationship tier act as entry points into the graph for bottom-up, keyword-based (exact match) searches.

Extraction uses a lightly guided strategy whereby the extraction process is seeded with a list of preferred entity classifications. The LLM is instructed to use an existing classification from the list before creating new ones. Any new classifications introduced by the LLM are then carried forward to subsequent invocations. This approach reduces but doesn't eliminate unwanted variations in entity classification.

Relationship values are currently freestyle (though relatively concise).

### Summarisation tier

This currently comprises `Topic`, `Statement` and `Fact` nodes. Proceeding from the bottom up:

#### Facts

A fact summarises a single triplet or triple-like unit of meaning. For example:

```
Property Graph model ACCESSED WITH openCypher
```

There are two types of fact: subject-predicate-object (SPO) facts, and subject-predicate-complement (SPC) facts. SPO facts are connected to entities in the subject and object positions. SPC facts are connected to subject entities only. Here's an example of an SPC fact:

```
Neptune Analytics PURPOSE analyze graph data
```

SPO facts are connected to other facts via `NEXT` relationships, where the object entity of a first fact acts as the subject entity for a subsequent fact.

Facts provide *connectivity across different sources*. It's not uncommon for an individual fact to be mentioned multiple times in the underlying corpus: for example, in a news articles dataset, a particular fact might be repeated in different news articles reporting on the same story. In the graph, there will be a single node to represent this specific fact. From this node it is then possible to traverse via statements, topics and chunks to all the places where that particular fact is mentioned.

Facts can, optionally, be embedded – and so as well as enhancing connectivity, they can also be used to provide a low-level, vector-based entry point into the graph. 

#### Statements

A statement or assertion extracted from the underlying sources. Statements are the *primary unit of context returned to the question answering LLM in the context window* – that is, the context comprises collections of statements grouped by source and topic.

Statements are typically associated with one or more facts (both SPO and SPC facts). For example:

```
Statement
---------
Neptune supports open graph APIs for property graphs (Gremlin and openCypher) and RDF graphs (SPARQL)

Facts
-----
SPARQL FOR RDF graphs
SPARQL API FOR RDF graphs
openCypher API FOR property graphs
Gremlin FOR property graphs
Gremlin API FOR property graphs
openCypher FOR property graphs
```

In some circumstances a statement may include one or more contextual *details* in addition to, or instead of, any associated facts. These contextual details take the same triplet form as facts, but they lack any entity (subject or object) relations, and so are inlined as a property in the statement node.

Statements are grouped beneath topics (see below). Within a particular topic, statements are also joined in a linked list via `PREVIOUS` relationships, making it easy to retrieve previous (and subsequent) statements belonging to the same underlying source.

Statements act as the primary unit of context for question-answering. They are connected transitively to other statements via both facts and topics.

Statements can, optionally, be embedded, and so can act as higher-level entry points in the graph based on a vector search. The vector-guided retriever uses statement embeddings to guide its search strategies. Statement embeddings also allow statements to be used in a 'baseline RAG' manner to retrieve relatively small pieces of context for answering simple questions.

#### Topics

A topic is a theme or area of focus within a specific source document. Source documents will typically have several topics. For example, one of the source documents in our Neptune documentation example has the following topics:

```
Neptune Analytics
Loading Graph Data into Amazon Neptune Analytics
```

Topics are scoped to individual source documents so as to provide connectivity across chunks within a single source. It's common for several chunks from the same source to be connected to the same topic.

Topics increase *connectivity between relevant chunks within a single source*, and provide a simple document-level summary mechanism.


