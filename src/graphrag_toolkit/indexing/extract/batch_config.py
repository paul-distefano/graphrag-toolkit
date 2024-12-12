# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class BatchJobVpcConfig:
    subnet_ids:List[str] = field(default_factory=list)
    security_group_ids:List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            'subnetIds': self.subnet_ids,
            'security_group_ids': self.security_group_ids
        }

@dataclass
class BatchConfig:
    role_arn:str 
    region:str
    bucket_name:str
    key_prefix:Optional[str]=None
    s3_encryption_key_id:Optional[str]=None
    vpc_config:Optional[BatchJobVpcConfig]=None
    max_batch_size:int=25000
    max_num_concurrent_batches:int=3