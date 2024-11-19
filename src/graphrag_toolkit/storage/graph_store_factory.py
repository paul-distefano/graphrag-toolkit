# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Union
from graphrag_toolkit.storage.graph_store import GraphStore, DummyGraphStore
from graphrag_toolkit.storage.neptune_graph_stores import NeptuneAnalyticsClient, NeptuneDatabaseClient

logger = logging.getLogger(__name__)

NEPTUNE_DATABASE = 'neptune-db://'
NEPTUNE_ANALYTICS = 'neptune-graph://'
DUMMY_GRAPH = 'graph://'

GraphStoreType = Union[str, GraphStore]
        
def graph_info_resolver(graph_info:str=None):

    NEPTUNE_DB_DNS = 'neptune.amazonaws.com'

    if not graph_info or graph_info.startswith(DUMMY_GRAPH):
        return (DUMMY_GRAPH, None)
    if graph_info.startswith(NEPTUNE_DATABASE):
        return (NEPTUNE_DATABASE, graph_info[len(NEPTUNE_DATABASE):])
    elif graph_info.startswith(NEPTUNE_ANALYTICS):
        return (NEPTUNE_ANALYTICS, graph_info[len(NEPTUNE_ANALYTICS):]) 
    elif graph_info.endswith(NEPTUNE_DB_DNS):
        return (NEPTUNE_DATABASE, graph_info)
    else:
        return (NEPTUNE_ANALYTICS, graph_info)  

class GraphStoreFactory():

    @staticmethod
    def for_graph_store(graph_info:GraphStoreType=None, **kwargs):

        if graph_info and isinstance(graph_info, GraphStore):
            return graph_info

        (graph_type, init_info) = graph_info_resolver(graph_info)

        if graph_type == NEPTUNE_DATABASE:
            logger.debug(f"Opening Neptune database [endpoint: {init_info}]")
            return GraphStoreFactory.for_neptune_database(init_info, **kwargs)
        elif graph_type == NEPTUNE_ANALYTICS:
            logger.debug(f"Opening Neptune Analytics graph [graph_id: {init_info}]")
            return GraphStoreFactory.for_neptune_analytics(init_info, **kwargs)
        else:
            logger.debug(f'Opening dummy graph store')
            return DummyGraphStore()
    
    @staticmethod
    def for_neptune_database(graph_endpoint, port=8182, **kwargs):
        endpoint_url = f'https://{graph_endpoint}' if ':' in graph_endpoint else f'https://{graph_endpoint}:{port}'
        return NeptuneDatabaseClient(endpoint_url=endpoint_url)
    
    @staticmethod
    def for_neptune_analytics(graph_id, **kwargs):
        return NeptuneAnalyticsClient(graph_id=graph_id)
    
    @staticmethod
    def for_dummy_graph_store(*args, **kwargs):
        return DummyGraphStore()