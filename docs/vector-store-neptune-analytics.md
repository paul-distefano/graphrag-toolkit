[[Home](./)]

## Neptune Analytics as a Vector Store

### Topics

  - [Overview](#overview)
  - [Creating a Neptune Analytics vector store](#creating-a-neptune-analytics-vector-store)

### Overview

You can use Amazon Neptune Analytics as a vector store.

### Creating a Neptune Analytics vector store

Use the `VectorStoreFactory.for_vector_store()` static factory method to create an instance of an Amazon Neptune Analytics vector store.

To create a Neptune Analytics vector store, supply a connection string that begins `neptune-graph://`, followed by the graph's identifier:

```python
from graphrag_toolkit.storage import VectorStoreFactory

neptune_connection_info = 'neptune-graph://g-jbzzaqb209'

vector_store = VectorStoreFactory.for_vector_store(neptune_connection_info)
```

