# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from dataclasses import dataclass
from typing import Optional

class MergeAction(Enum):
    MERGE_EXISTING = 1
    REPLACE_EXISTING = 2
    HALT_IF_EXISTING = 3

@dataclass
class InferClassificationsConfig:
    num_samples:Optional[int]=5
    num_iterations:Optional[int]=1
    merge_action:Optional[MergeAction]=MergeAction.HALT_IF_EXISTING