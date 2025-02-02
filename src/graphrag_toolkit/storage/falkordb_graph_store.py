# Copyright FalkorDB.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import falkordb
import string
import secrets
import json
import logging
import time
import uuid
from typing import Optional, Any, List, Union
from falkordb.node import Node
from falkordb.path import Path
from falkordb.graph import Graph
from redis.exceptions import ResponseError, AuthenticationError

from graphrag_toolkit.storage.graph_store import ( 
    GraphStore, NodeId, 
    format_id, RedactedGraphQueryLogFormatting)

logger = logging.getLogger(__name__)

def generate_random_alphabetic_string(length: int) -> str:
    """
    Generate a cryptographically secure random alphabetic string.

    :param length: Length of the generated string.
    :return: A random string of uppercase and lowercase letters.
    :raises ValueError: If length is non-positive.
    """
    if length <= 0:
        raise ValueError("Length must be a positive integer")
    
    characters = string.ascii_letters
    random_string = "".join(secrets.choice(characters) for _ in range(length))
    return random_string

class FalkorDBDatabaseClient(GraphStore):
    """
    Client for interacting with a FalkorDB database.

    Provides methods to connect to a FalkorDB instance, execute queries, and handle authentication.
    """
    def __init__(self,
                 endpoint_url: str = None,
                 database: Optional[str] = None,
                 username: str = None,
                 password: str = None,
                 ssl: bool = False,
                 _client: Optional[Any] = None,
                 *args,
                 **kwargs
                 ) -> None:
        """
        Initialize the FalkorDB database client.

        :param endpoint_url: URL of the FalkorDB instance.
        :param database: Name of the database to connect to.
        :param username: Username for authentication.
        :param password: Password for authentication.
        :param ssl: Whether to use SSL for the connection.
        :param _client: Optional existing client instance.
        """
        if username and not password:
            raise ValueError("Password is required when username is provided")
        
        if endpoint_url and not isinstance(endpoint_url, str):
            raise ValueError("Endpoint URL must be a string")
        
        if database is None:
            database = generate_random_alphabetic_string(4)

        if not database or not database.isalnum():
            raise ValueError("Database name must be alphanumeric and non-empty")

        super().__init__(*args, **kwargs)

        self.log_formatting = RedactedGraphQueryLogFormatting()  
        self.endpoint_url = endpoint_url
        self.database = database
        self.username = username
        self.password = password
        self.ssl = ssl
        self._client = _client
    
    @property
    def client(self) -> Graph:
        """
        Establish and return a FalkorDB client instance.

        :return: A FalkorDB Graph instance.
        :raises ConnectionError: If the connection to FalkorDB fails.
        """
        if self.endpoint_url:
            try:
                parts = self.endpoint_url.split(':')
                if len(parts) != 2:
                    raise ValueError("Invalid endpoint URL format. Expected format: "
                                     "'falkordb://host:port' or for local use 'falkordb://' ")
                self.host = parts[0]
                self.port = int(parts[1])
            except Exception as e:
                raise ValueError(f"Error parsing endpoint url: {e}") from e
        else:
            self.host = "localhost"
            self.port = 6379

        if self._client is None:
            try:
                self._driver = falkordb.FalkorDB(
                        host=self.host,
                        port=self.port,
                        username=self.username,
                        password=self.password,
                        ssl=self.ssl,
                    )
                self._client = self._driver.select_graph(self.database)
            except ConnectionError as e:
                logger.error(f"Failed to connect to FalkorDB: {e}")
                raise ConnectionError(f"Could not establish connection to FalkorDB: {e}") from e
            except AuthenticationError as e:
                logger.error(f"Authentication failed: {e}")
                raise ConnectionError(f"Authentication failed: {e}") from e
            except Exception as e:
                logger.error(f"Unexpected error while connecting to FalkorDB: {e}")
                raise ConnectionError(f"Unexpected error while connecting to FalkorDB: {e}") from e
        return self._client
    
    def node_id(self, id_name: str) -> NodeId:
        """
        Format a node identifier.

        :param id_name: Name of the node.
        :return: Formatted node identifier.
        """
        return format_id(id_name)

    def execute_query(self, 
                      cypher: str, 
                      parameters: Optional[dict] = None, 
                      correlation_id: Any = None) -> Union[List[List[Node]], List[List[List[Path]]]]:
        """
        Execute a Cypher query on the FalkorDB instance.

        :param cypher: The Cypher query to execute.
        :param parameters: Query parameters.
        :param correlation_id: Optional correlation ID for logging.
        :return: Query results as a list of nodes or paths.
        :raises ResponseError: If query execution fails.
        """
        if parameters is None:
            parameters = {}

        query_id = uuid.uuid4().hex[:5]

        request_log_entry_parameters = self.log_formatting.format_log_entry(
            self._logging_prefix(query_id, correlation_id), 
            cypher, 
            params=json.dumps(parameters),
        )

        logger.debug(f'[{request_log_entry_parameters.query_ref}] Query: [query: {request_log_entry_parameters.query}, parameters: {request_log_entry_parameters.parameters}]')

        start = time.time()

        try:
            response = self.client.query(
                q=request_log_entry_parameters.format_query_with_query_ref(cypher),
                params=parameters
            )
        except ResponseError as e:
            logger.error(f"Query execution failed: {e}. Query: {cypher}, Parameters: {parameters}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during query execution: {e}. Query: {cypher}, Parameters: {parameters}")
            raise ResponseError(f"Unexpected error during query execution: {e}") from e

        end = time.time()

        results = response.result_set

        if logger.isEnabledFor(logging.DEBUG):
            response_log_entry_parameters = self.log_formatting.format_log_entry(
                self._logging_prefix(query_id, correlation_id), 
                cypher, 
                parameters, 
                results
            )
            logger.debug(f'[{response_log_entry_parameters.query_ref}] {int((end-start) * 1000)}ms Results: [{response_log_entry_parameters.results}]')
        
        return results
