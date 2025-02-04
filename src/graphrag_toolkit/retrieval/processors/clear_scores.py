# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from graphrag_toolkit.retrieval.processors import ProcessorBase, ProcessorArgs
from graphrag_toolkit.retrieval.model import SearchResultCollection, SearchResult, Topic, Statement

from llama_index.core.schema import QueryBundle

class ClearScores(ProcessorBase):
    def __init__(self, args:ProcessorArgs):
        super().__init__(args)

    def _process_results(self, search_results:SearchResultCollection, query:QueryBundle) -> SearchResultCollection:
        def clear_statement_scores(topic:Topic):
            for s in topic.statements:
                if isinstance(s, Statement):
                    s.score = None
            return topic

        def clear_search_result_scores(index:int, search_result:SearchResult):
            search_result.score = None
            return self._apply_to_topics(search_result, clear_statement_scores)
        
        return self._apply_to_search_results(search_results, clear_search_result_scores)


