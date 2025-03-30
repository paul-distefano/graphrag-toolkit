[[Home](./)]

## Neptune Analytics as a Graph Store

### Topics

  - [Overview](#overview)
  - [Creating a Neptune Analytics graph store](#creating-a-neptune-analytics-graph-store)

### Overview

You can use Amazon Neptune Analytics as a graph store.

### Creating a Neptune Analytics graph store

Use the `GraphStoreFactory.for_graph_store()` static factory method to create an instance of a Neptune Analytics graph store.

To create a Neptune Analytics graph store, supply a connection string that begins `neptune-graph://`, followed by the graph's identifier:

```
from graphrag_toolkit.storage import GraphStoreFactory

neptune_connection_info = 'neptune-graph://g-jbzzaqb209'

graph_store = GraphStoreFactory.for_graph_store(neptune_connection_info)
```

