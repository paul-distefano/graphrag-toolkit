[[Home](./)]

## Constructing a Graph

There are two stages to graph construction: extract, and build. The graphrag-toolkit uses separate pipelines for each of these stages, plus micro-batching, to provide a continous ingest capability. This means that your graph will start being populated soon after extarction begins.

You can run the extract and build pipelines together, to provide for the continuous ingest described above. Or you can run the two pipelines separately, extracting first to file-based chunks, and then later building a graph from these chunks.

The `LexicalGraphIndex` is a convenience calss that allows you to run the extract and build pipelines together or separately. Alternatively, you can build your graph construction application using the underlying pipelines. This gives you more control over the configuration of each stage. We describe these two different approaches in the [Using the LexicalGraphIndex](#using-the-lexicalgraphindex) and [Advanced graph construction](#advanced-graph-construction) sections below.

### Using the LexicalGraphIndex

### Advanced graph construction

ConflictException
ConcurrentModificationException