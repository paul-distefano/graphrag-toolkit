# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import json
import logging
import boto3
from botocore.config import Config
from botocore.response import StreamingBody
from io import StringIO
from hashlib import sha256
from typing import Any
from llama_index.llms.bedrock import Bedrock
from llama_index.core.bridge.pydantic import Field

from graphrag_toolkit.utils.io_utils import read_json, write_json
from graphrag_toolkit.utils.bedrock_utils import *

logger = logging.getLogger(__name__)  
    
c_red, c_blue, c_green, c_cyan, c_norm = "\x1b[31m",'\033[94m','\033[92m', '\033[96m', '\033[0m'

class CacheBedrockClient:
    '''
    Encapsulates bedrock-runtime (Composition).
    Behaves like bedrock-runtime client.
    Adding control, caching and verbosity over invoke_model() calls made by llama_index
    '''
    
    def __init__(self, **kwargs: Any): 
        
        logger.debug('Making {} {}'.format(self.__class__.__name__,kwargs))
        
        # Control the cache
        self.enable_cache = kwargs.pop('enable_cache',False)
        
        # Control the verbosity
        self.verbose_prompt = kwargs.pop('verbose_prompt',False)
        self.verbose_response = kwargs.pop('verbose_response',False)
        
        config = (
                Config(
                    retries={"max_attempts": 5, "mode": "standard"},
                    connect_timeout=60,
                    read_timeout=60,
                )
        )
        
        self._client = boto3.Session().client("bedrock-runtime", config=config)
        self.exceptions = self._client.exceptions
        
    def invoke_model(self, modelId: str, body: str):
        '''Adding cache and verbosity over bedrock client'''
        if self.verbose_prompt:
            j = json.loads(body)
            logger.info(c_blue)
            logger.info(json.dumps(j, sort_keys=False, indent=4))
            logger.info(c_norm)
                        

        # Cache lookup
        if self.enable_cache:      
            cache_key = '{},{}'.format(modelId,body)
            cache_hex = sha256(cache_key.encode('utf-8')).hexdigest()
            cache_file = f'cache/bedrockchat/{modelId}/{cache_hex}.txt'

        
        if self.enable_cache and os.path.exists(cache_file):
            logger.debug('%sCached response %s%s', c_blue, cache_file, c_norm)
            response = read_json(cache_file)
            
        else:
            # Invoke the service
            response = self._client.invoke_model(modelId=modelId, body=body)
            
            # Stream to json
            response["body"] = json.loads(response["body"].read())
                        
            if self.enable_cache:
                write_json(cache_file,response)

        if self.verbose_response:
            for c in response["body"]['content']:
                logger.info(c_green,c['text'],c_norm)

        # Encode json back to stream
        body_str = json.dumps(response["body"])
        response["body"] = StreamingBody(StringIO(body_str),len(body_str))

        return response

class CacheBedrock(Bedrock):
    ''' 
    A wrapper over llama_index Bedrock.
    Using CacheBedrockClient.
    '''

    def __init__(self,model,**kwargs: Any): 

        cache_kwargs = {
            k:kwargs.pop(k)  
            for k in ['enable_cache', 'verbose_prompt','verbose_response']
            if k in kwargs
        }
            
        super().__init__(
            model=model,
            **kwargs
        )

        self._client = CacheBedrockClient(**cache_kwargs)
        


