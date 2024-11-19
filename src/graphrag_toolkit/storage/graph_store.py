# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import abc  
from dataclasses import dataclass
from tenacity import Retrying, stop_after_attempt, wait_random
from tenacity import RetryCallState
from typing import Callable, Dict, Any, Optional

from llama_index.core.bridge.pydantic import BaseModel

logger = logging.getLogger(__name__)

@dataclass
class NodeId:

    key:str
    value:str
    is_property_based:bool = True

    def __str__(self):
        return self.value
    
def format_id(id_name:str):
        parts = id_name.split('.')
        if len(parts) == 1:
            return NodeId(parts[0], parts[0])           
        else:
            return NodeId(parts[1], id_name)

def on_retry_query(
    logger: 'logging.Logger',
    log_level: int,
    exc_info: bool = False,
    query=None,
    properties={}
) -> Callable[[RetryCallState], None]:
    
    def log_it(retry_state: 'RetryCallState') -> None:
        local_exc_info: BaseException | bool | None

        if retry_state.outcome is None:
            raise RuntimeError('log_it() called before outcome was set')

        if retry_state.next_action is None:
            raise RuntimeError('log_it() called before next_action was set')

        if retry_state.outcome.failed:
            ex = retry_state.outcome.exception()
            verb, value = 'raised', f'{ex.__class__.__name__}: {ex}'

            if exc_info:
                local_exc_info = retry_state.outcome.exception()
            else:
                local_exc_info = False
        else:
            verb, value = 'returned', retry_state.outcome.result()
            local_exc_info = False  # exc_info does not apply when no exception

        logger.log(
            log_level,
            f'Retrying query in {retry_state.next_action.sleep} seconds because it {verb} {value} [attempt: {retry_state.attempt_number}, query: {query}, properties: {properties}]',
            exc_info=local_exc_info
        )

    return log_it

def on_query_failed(
    logger: 'logging.Logger',
    log_level: int,
    max_attempts: int,
    query=None, 
    properties={}
) -> Callable[['RetryCallState'], None]:
    
    def log_it(retry_state: 'RetryCallState') -> None:
        if retry_state.attempt_number == max_attempts:
            ex: BaseException | bool | None
            if retry_state.outcome.failed:
                ex = retry_state.outcome.exception()
                verb, value = 'raised', f'{ex.__class__.__name__}: {ex}'       
            logger.log(
                log_level,
                f'Query failed after {retry_state.attempt_number} retries because it {verb} {value} [query: {query}, properties: {properties}]',
                exc_info=ex
            )
        
    return log_it

class GraphStore(BaseModel):

    def execute_query_with_retry(self, query:str, properties:Dict[str, Any], max_attempts=3, max_wait=5, **kwargs):
        attempt_number = 0
        for attempt in Retrying(
            stop=stop_after_attempt(max_attempts), 
            wait=wait_random(min=0, max=max_wait),
            before_sleep=on_retry_query(logger, logging.WARNING, query=query, properties=properties), 
            after=on_query_failed(logger, logging.WARNING, max_attempts=max_attempts, query=query, properties=properties),
            reraise=True
        ):
            with attempt:
                attempt_number += 1
                attempt.retry_state.attempt_number
                self.execute_query(query, properties, **kwargs)

    def _logging_prefix(self, query_id:str, correlation_id:Optional[str]=None):
        return f'[{correlation_id}/{query_id}] ' if correlation_id else f'[{query_id}] ' 
    
    def node_id(self, id_name:str) -> NodeId:
        return format_id(id_name)
    
    @abc.abstractmethod
    def execute_query(self, cypher, parameters={}, correlation_id=None) -> Dict[str, Any]:
        raise NotImplementedError

    
class DummyGraphStore(GraphStore):
    def execute_query(self, cypher, parameters={}, correlation_id=None):  
        logger.debug(f'{self._logging_prefix(correlation_id)}query: {cypher}, parameters: {parameters}')
        return []
    