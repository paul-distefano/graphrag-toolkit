# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import Dict

from graphrag_toolkit.retrieval.processors import ProcessorBase, ProcessorArgs
from graphrag_toolkit.retrieval.model import SearchResultCollection, SearchResult, Topic

from llama_index.core.schema import QueryBundle

class FormatSources(ProcessorBase):
    def __init__(self, args:ProcessorArgs):
        super().__init__(args)

    def _process_results(self, search_results:SearchResultCollection, query:QueryBundle) -> SearchResultCollection:
        
        def format_source(index:int, search_result:SearchResult):
            search_result.source = ' '.join(search_result.source.metadata.values())
            return search_result
        
        return self._apply_to_search_results(search_results, format_source)


