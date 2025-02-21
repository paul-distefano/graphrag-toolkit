# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import hashlib
from typing import Optional

def get_hash(s):
    return hashlib.md5(s.encode('utf-8')).digest().hex()

def node_id_from(node_type:str, v1:str, v2:Optional[str]=None):
    if v2:
        return get_hash(f"{node_type.lower()}::{v1.lower().replace(' ', '_')}::{v2.lower().replace(' ', '_')}")
    else:
        return get_hash(f"{node_type.lower()}::{v1.lower().replace(' ', '_')}")    


    