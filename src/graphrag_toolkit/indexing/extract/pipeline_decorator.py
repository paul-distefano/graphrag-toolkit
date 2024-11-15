# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import abc
import six
from typing import Sequence

from llama_index.core.schema import BaseNode

@six.add_metaclass(abc.ABCMeta)
class PipelineDecorator():

    @abc.abstractmethod
    def handle_input_nodes(self, nodes:Sequence[BaseNode]):
        pass

    @abc.abstractmethod
    def handle_output_node(self, node: BaseNode) -> BaseNode:
        pass

