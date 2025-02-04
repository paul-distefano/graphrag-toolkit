# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import abc
from typing import Iterable, List

from graphrag_toolkit.indexing.model import SourceDocument

from llama_index.core.schema import BaseComponent

class SourceDocParser(BaseComponent):
     
    @abc.abstractmethod
    def _parse_source_docs(self, source_documents:Iterable[SourceDocument]) -> List[SourceDocument]:
        pass

    def parse_source_docs(self, source_documents:Iterable[SourceDocument]) -> List[SourceDocument]:
        return self._parse_source_docs(source_documents)