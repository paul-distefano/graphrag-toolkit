# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from graphrag_toolkit.retrieval.processors import ProcessorBase, ProcessorArgs
from graphrag_toolkit.retrieval.model import SearchResultCollection, SearchResult, Topic

from llama_index.core.schema import QueryBundle

class ClearStatementStrs(ProcessorBase):
    def __init__(self, args:ProcessorArgs):
        super().__init__(args)

    def _process_results(self, search_results:SearchResultCollection, query:QueryBundle) -> SearchResultCollection:
        
        def clear_statement_strs(topic:Topic):
            for statement in topic.statements:
                statement.statement_str = None
            return topic
    
        def clear_all_statement_strs(index:int, search_result:SearchResult):
            return self._apply_to_topics(search_result, clear_statement_strs)
        
        return self._apply_to_search_results(search_results, clear_all_statement_strs)