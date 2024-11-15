# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from .node_handler import NodeHandler
from .extract.constants import DEFAULT_TOPIC, SOURCE_DOC_KEY
from .build.constants import DEFAULT_CLASSIFICATION
from .utils.pipeline_utils import sink
from .utils.metadata_utils import last_accessed_date
from .utils.topic_utils import parse_extracted_topics
from .constants import (
    TRIPLES_KEY,
    PROPOSITIONS_KEY
)