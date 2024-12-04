# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import abc
import logging
from typing import Dict
from lru import LRU

from graphrag_toolkit.storage.graph_store import GraphStore

from llama_index.core.schema import BaseComponent, BaseNode

logger = logging.getLogger(__name__)

class GraphBuilder(BaseComponent):

    def _to_params(self, p:Dict):
        return { 'params': [p] }

    @classmethod
    @abc.abstractmethod
    def index_key(cls) -> str:
        pass

    @abc.abstractmethod
    def build(self, node:BaseNode, graph_client: GraphStore, node_ids:LRU):
        pass