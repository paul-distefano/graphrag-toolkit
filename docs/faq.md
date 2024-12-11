[[Home](./)]

## FAQ

### Errors and warnings

#### RuntimeError: Please use nest_asyncio.apply() to allow nested event loops

`nest_asyncio.apply()` provides a convenient solution to enable nested event loops and make it easier to handle complex asynchronous programming situations in Python. All of the code examples in the documentation include `nest_asyncio.apply()`. However, the examples are formatted to be run in a Jupyter notebook. If you’re building an application with a main entry point, you may encounter this runtime error. To fix, put your application logic inside a method, and add an `if name == 'main' block`:

```
import os

from graphrag_toolkit import LexicalGraphIndex
from graphrag_toolkit.storage import GraphStoreFactory
from graphrag_toolkit.storage import VectorStoreFactory

from llama_index.readers.web import SimpleWebPageReader

import nest_asyncio
nest_asyncio.apply()

def run_extract_and_build()

    graph_store = GraphStoreFactory.for_graph_store(
        'neptune-db://my-graph.cluster-abcdefghijkl.us-east-1.neptune.amazonaws.com'
    )
    
    vector_store = VectorStoreFactory.for_vector_store(
        'aoss://https://abcdefghijkl.us-east-1.aoss.amazonaws.com'
    )

    graph_index = LexicalGraphIndex(
        graph_store, 
        vector_store
    )

    doc_urls = [
        'https://docs.aws.amazon.com/neptune/latest/userguide/intro.html',
        'https://docs.aws.amazon.com/neptune-analytics/latest/userguide/what-is-neptune-analytics.html',
        'https://docs.aws.amazon.com/neptune-analytics/latest/userguide/neptune-analytics-features.html',
        'https://docs.aws.amazon.com/neptune-analytics/latest/userguide/neptune-analytics-vs-neptune-database.html'
    ]

    docs = SimpleWebPageReader(
        html_to_text=True,
        metadata_fn=lambda url:{'url': url}
    ).load_data(doc_urls)

    graph_index.extract_and_build(docs, show_progress=True)

if __name__ == '__main__':
    run_extract_and_build()
```

