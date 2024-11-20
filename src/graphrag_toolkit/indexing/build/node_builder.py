# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import abc
import six
from typing import Dict, List
from llama_index.core.schema import BaseNode, BaseComponent

from graphrag_toolkit.indexing.constants import DEFAULT_CLASSIFICATION

@six.add_metaclass(abc.ABCMeta)
class NodeBuilder(BaseComponent):

    @classmethod
    @abc.abstractmethod
    def name(cls) -> str:
        pass

    @classmethod
    @abc.abstractmethod
    def metadata_keys(cls) -> List[str]:
        pass
    
    @abc.abstractmethod
    def build_nodes(self, node:BaseNode, other_nodes:Dict[str, BaseNode]) -> List[BaseNode]:
        pass

    def allow_emit_node(self, node:BaseNode) -> bool:
        return True if node else False
    
    def _clean_id(self, s):
        return ''.join(c for c in s if c.isalnum())
        
    def _format_classification(self, classification):
        if not classification or classification == DEFAULT_CLASSIFICATION:
            return ''
        else:
            return f' ({classification})'
    
    def _format_fact(self, s, sc, p, o, oc):
        return f'{s} {p} {o}'
