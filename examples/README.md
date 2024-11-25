## Examples

### Notebooks

  - [**01-Combined Extract and Build**](./notebooks/01-Combined-Extract-and-Build.ipynb) – An example of [performing continuous ingest](https://github.com/awslabs/graphrag-toolkit/blob/main/docs/constructing-a-graph.md#continous-ingest-using-extract_and_build) using the `LexicalGraphINdex.extract_and_build()` method.
  - [**02-Separate Extract and Build**](./notebooks/02-Separate-Extract-and-Build.ipynb) – An example of [running the extract and build stages separately](https://github.com/awslabs/graphrag-toolkit/blob/main/docs/constructing-a-graph.md#run-the-extract-and-build-stages-separately), with intremdiate chunks persisted to the local filesystem using a `FileBasedChunks` object.
  - [**03-Advanced Construction**](./notebooks/03-Advanced-Construction.ipynb) – An example of [advanced graph construction](https://github.com/awslabs/graphrag-toolkit/blob/main/docs/constructing-a-graph.md#run-the-extract-and-build-stages-separately).
  - [**04-Querying**]](./notebooks/04-Querying.ipynb) – Examples of [querying the graph](https://github.com/awslabs/graphrag-toolkit/blob/main/docs/querying-the-graph.md) using the `LexicalGraphQueryEngine` with either the `TraversalBasedRetriever` or `SemanticGuidedRetriever`.
  
The notebooks assume that the [graph store and vector store connections](https://github.com/awslabs/graphrag-toolkit/blob/main/docs/storage-model.md) are stored in `GRAPH_STORE` and `VECTOR_STORE` environment variables. If you are running these notebooks via the Cloudformation template below, a `.env` file containing these variables will already have been installed in the Amazon SageMaker environment. If you are running these notebooks in a separate environment, you will need to populate these two environment variables.

### Cloudformation templates

[`graphrag-toolkit-stack.json`](./cloudformation-templates/graphrag-toolkit-stack.json) creates a graphrag-toolkit environment:

 - Amazon VPC with three private subnets, one public subnet, and an internet gateway
 - Amazon Neptune Database cluster with a single Neptune serverless instance
 - Amazon OpenSearch Serverless collection with a public endpoint
 - Amazon SageMaker notebook
 
Charges apply.

The SageMaker notebook's IAM role policy includes permissions that allow the following models to be invoked:

- `anthropic.claude-3-sonnet-20240229-v1:0`
- `cohere.embed-english-v3`

You must run the CloudFormation stack in a region containing these models, and must must [enable access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html) to these models before running the notebook examples.

The CloudFormation stack includes an input parameter, `IamPolicyArn`, that allows you to add an additional IAM policy to the GraphRAG client IAM role created by the stack. Use this parameter to add a custom policy containing permissions to additional resources that you want to use, such as specific Amazon S3 buckets, or additional Amazon Bedrock foundation models.