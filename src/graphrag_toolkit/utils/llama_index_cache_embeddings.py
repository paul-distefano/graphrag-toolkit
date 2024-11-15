# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
from hashlib import sha256
from typing import Literal
import logging
from llama_index.core.bridge.pydantic import Field
from llama_index.core.base.embeddings.base import Embedding
from llama_index.embeddings.bedrock import BedrockEmbedding

from graphrag_toolkit.utils.io_utils import read_text, write_text
from graphrag_toolkit.utils.bedrock_utils import *

logger = logging.getLogger(__name__)

c_red, c_blue, c_green, c_cyan, c_norm = "\x1b[31m",'\033[94m','\033[92m', '\033[96m', '\033[0m'    
            
class CacheBedrockEmbedding(BedrockEmbedding):

    enable_cache: bool = Field(description="Enable Bedrock embeddings cache.")

    def __init__(self, **kwargs: Any):       
        enable_cache = kwargs.pop('enable_cache',True)
        super().__init__(enable_cache=enable_cache, **kwargs)
    
    def _get_embedding(self, payload: str, type: Literal["text", "query"]) -> Embedding:
        """Call out to Bedrock embedding endpoint."""

        if self.enable_cache:
        
            cache_key = '{},{}'.format(payload,type)
            cache_hex = sha256(cache_key.encode('utf-8')).hexdigest()
            cache_file = f'cache/bedrock/{self.model_name}/{cache_hex}.txt'

            if os.path.exists(cache_file):
                vector = read_text(cache_file)
                logger.debug('%sCached embeddings %s%s', c_red, cache_file, c_norm)
                return eval(vector)


        vector = super()._get_embedding(payload=payload,type=type)

        if self.enable_cache:
            write_text(cache_file,str(vector))
            
        return vector    
