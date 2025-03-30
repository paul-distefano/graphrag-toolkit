[[Home](./)]

## Neptune Database as a Graph Store

### Topics

  - [Overview](#overview)
  - [Creating a Neptune Database graph store](#creating-a-neptune-database-graph-store)
    - [Connecting to Neptune via a proxy](#connecting-to-neptune-via-a-proxy)

### Overview

You can use Amazon Neptune Database as a graph store. The graphrag-toolkit requires [Neptune engine version](https://docs.aws.amazon.com/neptune/latest/userguide/engine-releases.html) 1.4.1.0 or later. 

### Creating a Neptune Database graph store

Use the `GraphStoreFactory.for_graph_store()` static factory method to create an instance of a Neptune Database graph store.

To create a Neptune Database graph store (engine version 1.4.1.0 or later), supply a connection string that begins `neptune-db://`, followed by an [endpoint](https://docs.aws.amazon.com/neptune/latest/userguide/feature-overview-endpoints.html):

```python
from graphrag_toolkit.storage import GraphStoreFactory

neptune_connection_info = 'neptune-db://mydbcluster.cluster-123456789012.us-east-1.neptune.amazonaws.com:8182'

graph_store = GraphStoreFactory.for_graph_store(neptune_connection_info)
```

#### Connecting to Neptune via a proxy

To connect to Neptune via a proxy (e.g. a load balancer), you must supply a config dictionary to the `GraphStoreFactory.for_graph_store()` factory method, with a `proxies` dictionary of proxy servers to use by protocol or endpoint:

```python
from graphrag_toolkit.storage import GraphStoreFactory

neptune_connection_info = 'neptune-db://mydbcluster.cluster-123456789012.us-east-1.neptune.amazonaws.com:8182'

config = {
    'proxies': {
        'http': 'http://proxy-hostname:80'
    }
}

graph_store = GraphStoreFactory.for_graph_store(
    neptune_connection_info,
    config=config
)
```
