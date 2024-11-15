from ragtime.base import call_api, REQ_GET, REQ_POST
from ragtime.llms import LLM
from ragtime.expe import QA, Prompt, LLMAnswer, Chunk
from ragtime.config import logger
from ragtime.prompters import Prompter
import re
import json
import os
from datetime import datetime, timedelta
import requests
from pydantic import Field
from typing import Dict, Any, ClassVar, List
from ragtime.retrievers import Retriever
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global constants
ALBERT_BASE_URL = os.environ.get('ALBERT_BASE_URL')
ALBERT_MODEL = "AgentPublic/llama3-instruct-guillaumetell"
DEFAULT_MAX_TOKENS = 2000
DEFAULT_TEMPERATURE = 0.7

logger = logging.getLogger(__name__)
SEARCH_USERNAME: str = "..."
SEARCH_PASSWORD: str = "..."
SEARCH_URL_LOGIN: str = "..."
SEARCH_URL_SEARCH: str = "..."

class Search(Retriever):
    """
    LSA Retriever queries reciTAL Search
    """
    token: str = "..."
    token_last_update: datetime = None
    TOKEN_DURATION: int = 1  # max token duration in hours

    def retrieve(self, qa: QA):
        """
        - the meta "team" contains the team filter to be sent to the retriever - it is a meta attached to the Question
        - it returns a chunk with the following meta fields:
            - text: chunk's text
            - score: confidence score
            - url: doc url on the right page
            - display_name: friendly version of the file name
            - page_number: page number of the chunk within the source document
            - image: url to the image representing the chunk
        """
        logger.debug(f'Start LSA Retriever')
        self._refresh_token()
        qa.chunks.empty()

        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token}"
        }

        params: Dict[str, Any] = {
            "query": qa.question.text
        }

        if "folder_id" in qa.question.meta:
            params["folder_id"] = qa.question.åmeta["folder_id"]

        try:
            response = requests.post(SEARCH_URL_SEARCH, headers=headers, params=params, json={})
            response.raise_for_status()
            search_results = response.json()
                        
            chunks = search_results.get("chunks", [])
            
            for i, search_chunk in enumerate(chunks):
                
                chunk = Chunk()
                
                # Try to extract text content
                if 'content' in search_chunk:
                    if isinstance(search_chunk['content'], dict):
                        chunk.text = search_chunk['content'].get('content', '')
                        chunk.meta["content_type"] = search_chunk['content'].get('content_type', 'unknown')
                    elif isinstance(search_chunk['content'], str):
                        chunk.text = search_chunk['content']
                        chunk.meta["content_type"] = 'text'
                    else:
                        logger.warning(f"Unexpected content format in chunk {i+1}")
                        continue
                else:
                    logger.warning(f"No 'content' field found in chunk {i+1}")
                    continue
                
                # Extract score
                chunk.meta["score"] = search_chunk.get('score', 0)
                chunk.meta["display_name"] = search_chunk.get('meta', {}).get('path','')
                chunk.meta["page_number"] = search_chunk.get('meta', {}).get('page','')
                
                # Extract other metadata
                for key, value in search_chunk.get("meta", {}).items():
                    if key != "explanation":
                        chunk.meta[key] = value
                
                qa.chunks.append(chunk)
                logger.debug(f"Successfully processed chunk {i+1}")
            
            logger.debug(f'Retrieved {len(qa.chunks)} chunk(s)')
        
        except requests.RequestException as e:
            logger.error(f"Error making request to LSA search API: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON response: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in retrieve method: {str(e)}")

    def _refresh_token(self):
        if (self.token != ""):
            self._token = self.token
        elif (self.token == "") or (datetime.now() - self.token_last_update).total_seconds() > self.TOKEN_DURATION * 3600:
            headers = {"Content-Type": "application/json"}
            data = {"username": SEARCH_USERNAME, "password": SEARCH_PASSWORD}
            response = requests.post(SEARCH_URL_LOGIN, json=data, headers=headers)
            response.raise_for_status()
            self._token = response.json()["access_token"]
            self._token_last_update = datetime.now()

class AlbertLLM_GuillaumeTellLLM(LLM):
    """Albert API LLM implementation"""
    name: str = ALBERT_MODEL
    prompter: Prompter = Field(..., description="Prompter instance")
    albert_model: ClassVar[str] = ALBERT_MODEL
    built_in_retriever: ClassVar[bool] = True
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float = DEFAULT_TEMPERATURE
    api_key: str = Field(default_factory=lambda: os.getenv('ALBERT_API_KEY'))
    _num_retries: int = 3
    
    def __init__(self, **data):
        """Initialize the Albert LLM client."""
        super().__init__(**data)
        if not self.api_key:
            raise ValueError("ALBERT_API_KEY environment variable is not set")

    @property
    def headers(self):
        return {
            'accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def get_collections(self):
        """Get available BGE model collections."""
        response = requests.get(
            f'{ALBERT_BASE_URL}/v1/collections',
            headers=self.headers
        )
        response.raise_for_status()
        collections = response.json()['data']
        return [
            coll for coll in collections 
            if coll['model'] == 'BAAI/bge-m3'
        ]

    def search_chunks(self, prompt: str, collection_ids: list, k: int = 5):
        """Search for relevant chunks."""
        payload = {
            "prompt": prompt,
            "collections": collection_ids,
            "k": k,
            "score_threshold": 0
        }
        
        response = requests.post(
            f'{ALBERT_BASE_URL}/v1/search',
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        
        chunks = []
        for item in response.json()['data']:
            chunk_data = {
                'text': item['chunk']['content'],  # Using 'text' as the key for compatibility
                'score': item['score'],
                'collection_id': item['chunk']['metadata'].get('collection_id'),
                'document_name': item['chunk']['metadata'].get('document_name'),
                'document_id': item['chunk']['metadata'].get('document_id')
            }
            chunks.append(chunk_data)
        return chunks

    def generate_answer(self, prompt: Prompt, context_chunks: list) -> str:
        """Generate answer using context chunks."""
        context = "\n\n".join([
            f"Chunk (score: {chunk['score']}):\n{chunk['text']}"
            for chunk in context_chunks
        ])
        
        messages = [
            {
                "role": "system",
                "content": f"{prompt.system}\n\nContext:\n{context}"
            },
            {
                "role": "user",
                "content": prompt.user
            }
        ]
        
        payload = {
            "messages": messages,
            "model": self.albert_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False
        }
        
        response = requests.post(
            f'{ALBERT_BASE_URL}/v1/chat/completions',
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']

    async def complete(self, prompt: Prompt) -> LLMAnswer:
        """Complete implementation for LLM base class."""
        retry: int = 1
        time_to_wait: float = 3.0
        start_ts = datetime.now()
        chunks = []

        while retry < self._num_retries:
            try:
                # Get collections and their IDs
                collections = self.get_collections()
                collection_ids = [coll['id'] for coll in collections]
                
                # Search for relevant chunks
                chunks = self.search_chunks(
                    prompt=prompt.user,
                    collection_ids=collection_ids
                )
                
                # Generate answer
                result = self.generate_answer(
                    prompt=prompt,
                    context_chunks=chunks
                )
                break
            except Exception as e:
                logger.debug(f"Exception occurred during API call, will retry {retry} of {self._num_retries}\nERROR:\n{e}")
                await asyncio.sleep(time_to_wait)
                retry += 1
                if retry >= self._num_retries:
                    raise

        duration = (datetime.now() - start_ts).total_seconds()
        
        return LLMAnswer(
            name=self.name,
            prompt=prompt,
            text=result,
            full_name=self.name,
            timestamp=start_ts,
            duration=duration,
            chunks=chunks,
            cost=None
        )

class AlbertLLM_Llama3InstructLLM(LLM):
    """Albert API LLM implementation"""
    name: str = "AgentPublic/llama3-instruct-8b"
    prompter: Prompter = Field(..., description="Prompter instance")
    albert_model: ClassVar[str] = "AgentPublic/llama3-instruct-8b"
    built_in_retriever: ClassVar[bool] = True
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float = DEFAULT_TEMPERATURE
    api_key: str = Field(default_factory=lambda: os.getenv('ALBERT_API_KEY'))
    _num_retries: int = 3
    
    def __init__(self, **data):
        """Initialize the Albert LLM client."""
        super().__init__(**data)
        if not self.api_key:
            raise ValueError("ALBERT_API_KEY environment variable is not set")

    @property
    def headers(self):
        return {
            'accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def get_collections(self):
        """Get available BGE model collections."""
        response = requests.get(
            f'{ALBERT_BASE_URL}/v1/collections',
            headers=self.headers
        )
        response.raise_for_status()
        collections = response.json()['data']
        return [
            coll for coll in collections 
            if coll['model'] == 'BAAI/bge-m3'
        ]

    def search_chunks(self, prompt: str, collection_ids: list, k: int = 5):
        """Search for relevant chunks."""
        payload = {
            "prompt": prompt,
            "collections": collection_ids,
            "k": k,
            "score_threshold": 0
        }
        
        response = requests.post(
            f'{ALBERT_BASE_URL}/v1/search',
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        
        chunks = []
        for item in response.json()['data']:
            chunk_data = {
                'text': item['chunk']['content'],  # Using 'text' as the key for compatibility
                'score': item['score'],
                'collection_id': item['chunk']['metadata'].get('collection_id'),
                'document_name': item['chunk']['metadata'].get('document_name'),
                'document_id': item['chunk']['metadata'].get('document_id')
            }
            chunks.append(chunk_data)
        return chunks

    def generate_answer(self, prompt: Prompt, context_chunks: list) -> str:
        """Generate answer using context chunks."""
        context = "\n\n".join([
            f"Chunk (score: {chunk['score']}):\n{chunk['text']}"
            for chunk in context_chunks
        ])
        
        messages = [
            {
                "role": "system",
                "content": f"{prompt.system}\n\nContext:\n{context}"
            },
            {
                "role": "user",
                "content": prompt.user
            }
        ]
        
        payload = {
            "messages": messages,
            "model": self.albert_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False
        }
        
        response = requests.post(
            f'{ALBERT_BASE_URL}/v1/chat/completions',
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']

    async def complete(self, prompt: Prompt) -> LLMAnswer:
        """Complete implementation for LLM base class."""
        retry: int = 1
        time_to_wait: float = 3.0
        start_ts = datetime.now()
        chunks = []

        while retry < self._num_retries:
            try:
                # Get collections and their IDs
                collections = self.get_collections()
                collection_ids = [coll['id'] for coll in collections]
                
                # Search for relevant chunks
                chunks = self.search_chunks(
                    prompt=prompt.user,
                    collection_ids=collection_ids
                )
                
                # Generate answer
                result = self.generate_answer(
                    prompt=prompt,
                    context_chunks=chunks
                )
                break
            except Exception as e:
                logger.debug(f"Exception occurred during API call, will retry {retry} of {self._num_retries}\nERROR:\n{e}")
                await asyncio.sleep(time_to_wait)
                retry += 1
                if retry >= self._num_retries:
                    raise

        duration = (datetime.now() - start_ts).total_seconds()
        
        return LLMAnswer(
            name=self.name,
            prompt=prompt,
            text=result,
            full_name=self.name,
            timestamp=start_ts,
            duration=duration,
            chunks=chunks,
            cost=None
        )
    
class AlbertLLM_Llama31InstructLLM(LLM):
    """Albert API LLM implementation"""
    name: str = "AgentPublic/Llama-3.1-8B-Instruct"
    prompter: Prompter = Field(..., description="Prompter instance")
    albert_model: ClassVar[str] = "AgentPublic/Llama-3.1-8B-Instruct"
    built_in_retriever: ClassVar[bool] = True
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float = DEFAULT_TEMPERATURE
    api_key: str = Field(default_factory=lambda: os.getenv('ALBERT_API_KEY'))
    _num_retries: int = 3
    
    def __init__(self, **data):
        """Initialize the Albert LLM client."""
        super().__init__(**data)
        if not self.api_key:
            raise ValueError("ALBERT_API_KEY environment variable is not set")

    @property
    def headers(self):
        return {
            'accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def get_collections(self):
        """Get available BGE model collections."""
        response = requests.get(
            f'{ALBERT_BASE_URL}/v1/collections',
            headers=self.headers
        )
        response.raise_for_status()
        collections = response.json()['data']
        return [
            coll for coll in collections 
            if coll['model'] == 'BAAI/bge-m3'
        ]

    def search_chunks(self, prompt: str, collection_ids: list, k: int = 5):
        """Search for relevant chunks."""
        payload = {
            "prompt": prompt,
            "collections": collection_ids,
            "k": k,
            "score_threshold": 0
        }
        
        response = requests.post(
            f'{ALBERT_BASE_URL}/v1/search',
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        
        chunks = []
        for item in response.json()['data']:
            chunk_data = {
                'text': item['chunk']['content'],  # Using 'text' as the key for compatibility
                'score': item['score'],
                'collection_id': item['chunk']['metadata'].get('collection_id'),
                'document_name': item['chunk']['metadata'].get('document_name'),
                'document_id': item['chunk']['metadata'].get('document_id')
            }
            chunks.append(chunk_data)
        return chunks

    def generate_answer(self, prompt: Prompt, context_chunks: list) -> str:
        """Generate answer using context chunks."""
        context = "\n\n".join([
            f"Chunk (score: {chunk['score']}):\n{chunk['text']}"
            for chunk in context_chunks
        ])
        
        messages = [
            {
                "role": "system",
                "content": f"{prompt.system}\n\nContext:\n{context}"
            },
            {
                "role": "user",
                "content": prompt.user
            }
        ]
        
        payload = {
            "messages": messages,
            "model": self.albert_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False
        }
        
        response = requests.post(
            f'{ALBERT_BASE_URL}/v1/chat/completions',
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']

    async def complete(self, prompt: Prompt) -> LLMAnswer:
        """Complete implementation for LLM base class."""
        retry: int = 1
        time_to_wait: float = 3.0
        start_ts = datetime.now()
        chunks = []

        while retry < self._num_retries:
            try:
                # Get collections and their IDs
                collections = self.get_collections()
                collection_ids = [coll['id'] for coll in collections]
                
                # Search for relevant chunks
                chunks = self.search_chunks(
                    prompt=prompt.user,
                    collection_ids=collection_ids
                )
                
                # Generate answer
                result = self.generate_answer(
                    prompt=prompt,
                    context_chunks=chunks
                )
                break
            except Exception as e:
                logger.debug(f"Exception occurred during API call, will retry {retry} of {self._num_retries}\nERROR:\n{e}")
                await asyncio.sleep(time_to_wait)
                retry += 1
                if retry >= self._num_retries:
                    raise

        duration = (datetime.now() - start_ts).total_seconds()
        
        return LLMAnswer(
            name=self.name,
            prompt=prompt,
            text=result,
            full_name=self.name,
            timestamp=start_ts,
            duration=duration,
            chunks=chunks,
            cost=None
        )