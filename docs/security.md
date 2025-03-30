[[Home](./)]

## Security

### Topics

  - [Overview](#overview)
  - [Managing access to Amazon Neptune](#managing-access-to-amazon-neptune)
  - [Managing access to Amazon OpenSearch Serverless](#managing-access-to-amazon-opensearch-serverless)
    - [OpenSearch API operations IAM policy](#opensearch-api-operations-iam-policy)
    - [Data access policy](#data-access-policy)
    - [Network access policy](#network-access-policy)
    - [Encryption policy](#encryption-policy)
  - [Managing access to Amazon Bedrock](#managing-access-to-amazon-bedrock)
  
### Overview

When building an application with the graphrag-toolkit, you are responsible for securing access to your source data, and to the graph store, vector store, and foundation model APIs that you use. The following sections provide guidance on using AWS Identity and Access Management (IAM) policies to control access to Amazon Neptune, Amazon OpenSearch Serverless, and Amazon Bedrock.

### Managing access to Amazon Neptune

Index operations require read and write access to your Amazon Neptune database. Query operations require only read access to the database.

To allow your application to read data from an Amazon Neptune database, attach the following example IAM policy to the AWS identity under which your application runs. Replace `<account-id>` with your AWS account ID, `<region>` with the name of the AWS Region in which your Amazon Neptune database cluster is located, and `<cluster-resource-id>` with the [cluster resource id](https://docs.aws.amazon.com/neptune/latest/userguide/iam-data-resources.html) of your database cluster.

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "NeptuneDBReadAccessStatement",
            "Effect": "Allow",
            "Action": [
                "neptune-db:ReadDataViaQuery"
            ],
            "Resource": "arn:aws:neptune-db:<region>:<account-id>:<cluster-resource-id>/*",
            "Condition": {
                "StringEquals": {
                    "neptune-db:QueryLanguage": "OpenCypher"
                }
            }
        }
    ]
}
```

To allow your application to write data to an Amazon Neptune database, attach the following example IAM policy to the AWS identity under which your application runs. Replace `<account-id>` with your AWS account ID, `<region>` with the name of the AWS Region in which your Amazon Neptune database cluster is located, and `<cluster-resource-id>` with the [cluster resource id](https://docs.aws.amazon.com/neptune/latest/userguide/iam-data-resources.html) of your database cluster.

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "NeptuneDBWriteAccessStatement",
            "Effect": "Allow",
            "Action": [
                "neptune-db:WriteDataViaQuery"
            ],
            "Resource": "arn:aws:neptune-db:<region>:<account-id>:<cluster-resource-id>/*",
            "Condition": {
                "StringEquals": {
                    "neptune-db:QueryLanguage": "OpenCypher"
                }
            }
        }
    ]
}
```

See [Managing access to Amazon Neptune databases using IAM policies](https://docs.aws.amazon.com/neptune/latest/userguide/security-iam-access-manage.html) for more details on protecting access to Amazon Neptune using IAM policies.

### Managing access to Amazon OpenSearch Serverless

To allow your application to read from and write data to an Amazon OpenSearch Serverless collection, you must associate data access, network and encryption policies with the collection. On top of that, an associated principal must also be granted access to the IAM permission `aoss:APIAccessAll`, which you can do using an IAM policy.

See [Overview of security in Amazon OpenSearch Serverless](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-security.html) for more details on protecting access to Amazon OpenSearch Serverless collections.

#### OpenSearch API operations IAM policy

To allow data plane access to the OpenSearch API operations, attach the following example IAM policy to the AWS identity under which your application runs. Replace `<account-id>` with your AWS account ID, `<region>` with the name of the AWS Region in which your Amazon OpenSearch Serverless collection is located, and `<collection-id>` with the id (not the name) of your collection.

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "OpenSearchServerlessAPIAccessAllStatement",
            "Effect": "Allow",
            "Action": [
                "aoss:APIAccessAll"
            ],
            "Resource": [
                "arn:aws:aoss:<region>:<account>:collection/<collection-id>"
            ]
        }
    ]
}
```

#### Data access policy

A [data access policy](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-data-access.html) controls access to the OpenSearch operations that OpenSearch Serverless supports.

You can use an existing data access policy or you can create a new one using the example policy below. Replace `<collection-name>` with the name of your OpenSearch Serverless collection, and `<principal-arn>` with the ARN of the IAM role or user attached to your application.

```
[
    {
        "Rules": [
            {
                "Resource": [
                    "collection/<collection-name>"
                ],
                "Permission": [
                    "aoss:DescribeCollectionItems",
                    "aoss:CreateCollectionItems",
                    "aoss:UpdateCollectionItems"
                ],
                "ResourceType": "collection"
            },
            {
                "Resource": [
                    "index/<collection-name>/*"
                ],
                "Permission": [
                    "aoss:UpdateIndex",
                    "aoss:DescribeIndex",
                    "aoss:ReadDocument",
                    "aoss:WriteDocument",
                    "aoss:CreateIndex"
                ],
                "ResourceType": "index"
            }
        ],
        "Principal": [
            "<principal-arn>"
        ]
    }
]
```

#### Network access policy

A [network access policy](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-network.html) defines network access to an OpenSearch Serverless collection's endpoint. The network settings for an Amazon OpenSearch Serverless collection determine whether the collection is accessible over the internet from public networks, or whether it must be accessed privately via a VPC endpoint. 

You can use an existing network access policy or you can create a new one using the example policy below. This example policy provides public access to a collection's OpenSearch endpoint. Replace `<collection-name>` with the name of your OpenSearch Serverless collection:

```
[
    {
        "Rules": [
            {
                "Resource": [
                    "collection/<collection-name>"
                ],
                "ResourceType": "collection"
            }
        ],
        "AllowFromPublic": true
    }
]
```

#### Encryption policy

An [encryption policy](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-encryption.html) assigns an encryption key to the collection. Collections are encrypted using either an AWS owned key or a customer managed key. 

You can use an existing encryption policy or you can create a new one using the example policy below. This example policy uses an AWS owned key to encrypt a collection. Replace `<collection-name>` with the name of your OpenSearch Serverless collection:

```
[
    {
        "Rules":[
          {
              "ResourceType":"collection",
              "Resource":[
                  "collection/<collection-name>"
              ]
          }
      ],
      "AWSOwnedKey": true
    }
]
```

### Managing access to Amazon Bedrock

To allow your application to invoke the Amazon Bedrock foundation models used by the graphrag-toolkit, attach the following example IAM policy to the AWS identity under which your application runs. Replace `<region>` with the name of the AWS Region in which Amazon Bedrock is located.
  
This example IAN policy assumes that you are using the toolkit's default models: `anthropic.claude-3-sonnet-20240229-v1:0` and `cohere.embed-english-v3`. Before running your applictaion, you must [enable access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html) to these models.

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "BedrockInvokeModelStatement",
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": [
                "arn:aws:bedrock:<region>::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
                "arn:aws:bedrock:<region>::foundation-model/cohere.embed-english-v3"
            ]
        }
    ]
}
```