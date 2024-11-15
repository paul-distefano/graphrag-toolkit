# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import boto3
import json
import os
import io
import uuid
import logging
import shutil
import hashlib
from typing import Callable, Dict, Any
from os.path import join
from urllib.parse import urlparse

from graphrag_toolkit.indexing.extract.id_rewriter import IdRewriter
from graphrag_toolkit.indexing.extract.constants import SOURCE_DOC_KEY

from llama_index.core.schema import TextNode, Document
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo

logger = logging.getLogger(__name__)

class TempFile():
    def __init__(self, filepath):
        self.filepath = filepath
        
    def __enter__(self):
        self.file = open(self.filepath)
        return self
    
    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.file.close()
        os.remove(self.filepath)
        
    def readline(self):
        return self.file.readline()
    
class TempDir():
    def __init__(self, dir_path):
        self.dir_path = dir_path
        
    def __enter__(self):
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)
        return self
    
    def __exit__(self, exception_type, exception_value, exception_traceback):
        if os.path.exists(self.dir_path):
            shutil.rmtree(self.dir_path)

class BedrockKnowledgeBaseExport():

    def __init__(self, 
                 bucket, 
                 keys=[], 
                 region='us-east-1', 
                 limit=-1, 
                 output_dir='output', 
                 metadata_fn:Callable[[str], Dict[str, Any]]=None, 
                 **kwargs):
        
        self.bucket=bucket
        self.keys=keys if isinstance(keys, list) else [keys]
        self.region=region
        self.limit=limit
        self.output_dir = output_dir
        self.s3 = boto3.client('s3', region_name=self.region)
        self.id_rewriter = IdRewriter()
        self.metadata_fn=metadata_fn
        
    def _kb_chunks(self, kb_export_dir):
        
        for key in self.keys:
        
            logger.info(f'Loading Amazon Bedrock Knowledge Base export file [bucket: {self.bucket}, key: {key}, region: {self.region}]')

            temp_filepath = join(kb_export_dir, f'{uuid.uuid4().hex}.json')
            self.s3.download_file(self.bucket, key, temp_filepath)

            with TempFile(temp_filepath) as f:
                while True:
                    line = f.readline()
                    if not line:
                        break
                    else:
                        yield json.loads(line)
                        
    def _parse_key(self, source):
        
        parsed = urlparse(source, allow_fragments=False)
        return parsed.path.lstrip('/')
    
    def _download_source_doc(self, source, doc_file_path):

        key = self._parse_key(source)

        logger.info(f'Loading Amazon Bedrock Knowledge Base underyling source document [source: {source}, bucket: {self.bucket}, key: {key}, region: {self.region}]')
            
        with io.BytesIO() as io_stream:
            self.s3.download_fileobj(self.bucket, key, io_stream)
    
            io_stream.seek(0)
            data = io_stream.read().decode('utf-8')
        
        metadata = self.metadata_fn(data) if self.metadata_fn else {}
        if not metadata:
            metadata = { 'source': source }
        elif not metadata['source']:
            metadata['source'] = source
        
        doc = Document(
            text=data,
            metadata=metadata
        )
        
        doc = self.id_rewriter([doc])[0]
        
        with open(doc_file_path, 'w') as f:
                f.write(doc.to_json())
        
        return doc
    
    def _open_source_doc(self, doc_file_path):
        with open(doc_file_path) as f:
            data = json.load(f)
            return Document.from_dict(data)

    def _get_doc_temp_filename(self, source):
        return hashlib.md5(source.encode('utf-8')).digest().hex()
    
    def _get_source_doc(self, source_docs_dir, source):
        
        publish_doc = False
        doc = None
        
        doc_file_path = join(source_docs_dir, self._get_doc_temp_filename(source))
        
        if os.path.exists(doc_file_path):
            doc = self._open_source_doc(doc_file_path)
        else:
            doc = self._download_source_doc(source, doc_file_path)
            publish_doc = True

        return (publish_doc, doc)
    
    def _get_doc_count(self, source_docs_dir):
        doc_count = len([name for name in os.listdir(source_docs_dir) if os.path.isfile(name)]) - 1
        logger.info(f'doc_count: {doc_count}')
        return doc_count
    
    def chunks(self):
        return self
    
    def __iter__(self):

        job_dir = join(self.output_dir, 'bedrock-kb', f'{uuid.uuid4().hex}')
        kb_export_dir = join(job_dir, 'kb-export')
        source_docs_dir = join(job_dir, 'source-docs')
        
        logger.info(f'Creating Amazon Bedrock Knowledge Base temp directories [kb_export_dir: {kb_export_dir}, source_docs_dir: {source_docs_dir}]')

        doc = None
        count = 0
        
        with TempDir(kb_export_dir) as k:
            with TempDir(source_docs_dir) as s:
        
                for kb_chunk in self._kb_chunks(kb_export_dir):
                    
                    bedrock_id = kb_chunk['id']
                    metadata = json.loads(kb_chunk['AMAZON_BEDROCK_METADATA'])
                    source = metadata['source']
                    
                    chunk = TextNode()
                    
                    
                    chunk.text = kb_chunk['AMAZON_BEDROCK_TEXT_CHUNK']
                    chunk.metadata = metadata
                    chunk.metadata['bedrock_id'] = bedrock_id
                    
                    (publish_doc, doc) = self._get_source_doc(source_docs_dir, source)
        
                    chunk.embedding = kb_chunk['bedrock-knowledge-base-default-vector']
                    chunk.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(
                        node_id=doc.id_,
                        node_type=NodeRelationship.SOURCE,
                        metadata=doc.metadata,
                        hash=doc.hash
                    )
                    
                    logger.debug(f'Emitting chunk for Amazon Bedrock Knowledge Base entry: [source: {source}, doc.id: {doc.id_}, chunk.id: {chunk.id_}, publish_doc: {publish_doc}]')
                    
                    if publish_doc:
                        chunk.metadata[SOURCE_DOC_KEY] = doc
                    
                    yield chunk

                    count += 1
                    if self.limit > 0 and count >= self.limit:
                        break