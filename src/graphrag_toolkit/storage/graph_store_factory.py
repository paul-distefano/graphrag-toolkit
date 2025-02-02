# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Union
from graphrag_toolkit.storage.graph_store import GraphStore, DummyGraphStore, GraphQueryLogFormatting, RedactedGraphQueryLogFormatting
from graphrag_toolkit.storage.neptune_graph_stores import NeptuneAnalyticsClient, NeptuneDatabaseClient
from graphrag_toolkit.storage.falkordb_graph_store import FalkorDBDatabaseClient

logger = logging.getLogger(__name__)

NEPTUNE_DATABASE = 'neptune-db://'
NEPTUNE_ANALYTICS = 'neptune-graph://'
FALKORDB = 'falkordb://'
DUMMY_GRAPH = 'graph://'

GraphStoreType = Union[str, GraphStore]

def graph_info_resolver(graph_info:str=None):
    NEPTUNE_DB_DNS = 'neptune.amazonaws.com'
    FALKORDB_DNS = 'falkordb.com'

    if not graph_info or graph_info.startswith(DUMMY_GRAPH):
        return (DUMMY_GRAPH, None)
    if graph_info.startswith(NEPTUNE_DATABASE):
        return (NEPTUNE_DATABASE, graph_info[len(NEPTUNE_DATABASE):])
    elif graph_info.startswith(NEPTUNE_ANALYTICS):
        return (NEPTUNE_ANALYTICS, graph_info[len(NEPTUNE_ANALYTICS):]) 
    elif graph_info.startswith(FALKORDB):
        return (FALKORDB, graph_info[len(FALKORDB):])
    elif graph_info.endswith(NEPTUNE_DB_DNS):
        return (NEPTUNE_DATABASE, graph_info)
    elif graph_info.endswith(FALKORDB_DNS):
        return (FALKORDB, graph_info)
    else:
        return (NEPTUNE_ANALYTICS, graph_info)

def get_log_formatting(args):
    log_formatting = args.pop('log_formatting', RedactedGraphQueryLogFormatting())
    if not isinstance(log_formatting, GraphQueryLogFormatting):
        raise ValueError('log_formatting must be of type GraphQueryLogFormatting')
    return log_formatting

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
        elif graph_type == FALKORDB:
            logger.debug(f"Opening FalkorDB database [endpoint: {init_info}]")
            return GraphStoreFactory.for_falkordb(init_info, **kwargs)
        else:
            logger.debug('Opening dummy graph store')
            return DummyGraphStore()

    @staticmethod
    def for_neptune_database(graph_endpoint, port=8182, **kwargs):
        endpoint_url = f'https://{graph_endpoint}' if ':' in graph_endpoint else f'https://{graph_endpoint}:{port}'
        return NeptuneDatabaseClient(endpoint_url=endpoint_url, log_formatting=get_log_formatting(kwargs))

    @staticmethod
    def for_neptune_analytics(graph_id, **kwargs):
        log_formatting = kwargs.pop('log_formattings', RedactedGraphQueryLogFormatting())
        if not isinstance(log_formatting, GraphQueryLogFormatting):
            raise ValueError('log_formatting must be of type GraphQueryLogFormatting')
        return NeptuneAnalyticsClient(graph_id=graph_id, log_formatting=get_log_formatting(kwargs))

    @staticmethod
    def for_falkordb(graph_endpoint, **kwargs):
        """
        Initializes and returns the FalkorDB database client.
        """
        return FalkorDBDatabaseClient(endpoint_url=graph_endpoint, log_formatting=get_log_formatting(kwargs))

    @staticmethod
    def for_dummy_graph_store(*args, **kwargs):
        return DummyGraphStore(log_formatting=get_log_formatting(kwargs))
