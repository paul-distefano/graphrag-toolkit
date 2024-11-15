# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import boto3
import json
import logging
import time
import uuid
from botocore.config import Config
from typing import Optional, Any

from graphrag_toolkit.storage.graph_store import GraphStore, NodeId

from llama_index.core.bridge.pydantic import PrivateAttr

logger = logging.getLogger(__name__)

NUM_CHARS_IN_DEBUG_RESULTS = 256

def format_id_for_neptune(id_name:str):
        parts = id_name.split('.')
        if len(parts) == 1:
            return NodeId(parts[0], '`~id`', False)           
        else:
            return NodeId(parts[1], f'id({parts[0]})', False)

class NeptuneAnalyticsClient(GraphStore):
    
    graph_id: str
    _client: Optional[Any] = PrivateAttr(default=None)
        
    def __getstate__(self):
        self._client = None
        return super().__getstate__()

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                'neptune-graph', 
                config=(Config(retries={'total_max_attempts': 1, 'mode': 'standard'}, read_timeout=600))
            )
        return self._client
    
    def node_id(self, id_name:str) -> NodeId:
        return format_id_for_neptune(id_name)
 
    def execute_query(self, cypher, parameters={}, correlation_id=None):

        query_id = uuid.uuid4().hex[:5]

        logger.debug(f'{self._logging_prefix(query_id, correlation_id)}Query: [graphId: {self.graph_id}, query: {cypher}, parameters: {parameters}]')

        start = time.time()
        
        response =  self.client.execute_query(
            graphIdentifier=self.graph_id,
            queryString=cypher,
            parameters=parameters,
            language='OPEN_CYPHER',
            planCache='DISABLED'
        )

        end = time.time()

        results = json.loads(response['payload'].read())['results']

        if logger.isEnabledFor(logging.DEBUG):
            results_str = str(results)
            if len(results_str) > NUM_CHARS_IN_DEBUG_RESULTS:
                results_str = f'{results_str[:NUM_CHARS_IN_DEBUG_RESULTS]}... <{len(results_str) - NUM_CHARS_IN_DEBUG_RESULTS} more chars>'
            logger.debug(f'{self._logging_prefix(query_id, correlation_id)}{int((end-start) * 1000)}ms Results: [{results_str}]')
    
        return results
    
class NeptuneDatabaseClient(GraphStore):
            
    endpoint_url: str
    _client: Optional[Any] = PrivateAttr(default=None)
        
    def __getstate__(self):
        self._client = None
        return super().__getstate__()

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                'neptunedata', 
                endpoint_url=self.endpoint_url,
                config=(Config(retries={'total_max_attempts': 1, 'mode': 'standard'}, read_timeout=600))
            )
        return self._client
    
    def node_id(self, id_name:str) -> NodeId:
        return format_id_for_neptune(id_name)

    def execute_query(self, cypher, parameters={}, correlation_id=None):

        query_id = uuid.uuid4().hex[:5]
        
        params = json.dumps(parameters)

        logger.debug(f'{self._logging_prefix(query_id, correlation_id)}Query: [query: {cypher}, parameters: {params}]')

        start = time.time()

        response =  self.client.execute_open_cypher_query(
            openCypherQuery=cypher,
            parameters=params
        )

        end = time.time()

        results = response['results']

        if logger.isEnabledFor(logging.DEBUG):
            results_str = str(results)
            if len(results_str) > NUM_CHARS_IN_DEBUG_RESULTS:
                results_str = f'{results_str[:NUM_CHARS_IN_DEBUG_RESULTS]}... <{len(results_str) - NUM_CHARS_IN_DEBUG_RESULTS} more chars>'
            logger.debug(f'{self._logging_prefix(query_id, correlation_id)}{int((end-start) * 1000)}ms Results: [{results_str}]')
    
        return results