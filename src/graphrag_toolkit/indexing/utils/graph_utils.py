# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import hashlib

def get_hash(s):
    return hashlib.md5(s.encode('utf-8')).digest().hex()

def node_id_from(name, label=None):
    if label:
        return get_hash(f"{name.lower().replace(' ', '_')}::{label.lower().replace(' ', '_')}")
    else:
        return get_hash(f"{name.lower().replace(' ', '_')}")    


    