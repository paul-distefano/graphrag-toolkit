# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from .node_handler import NodeHandler
from .extract.constants import DEFAULT_TOPIC, SOURCE_DOC_KEY
from .build.constants import DEFAULT_CLASSIFICATION
from .utils.pipeline_utils import sink
from .utils.metadata_utils import last_accessed_date
from .constants import TOPICS_KEY, PROPOSITIONS_KEY, DEFAULT_ENTITY_CLASSIFICATIONS