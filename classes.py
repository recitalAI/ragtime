from ragtime.base import call_api, REQ_GET, REQ_POST
from ragtime.llms import LLM
from ragtime.expe import QA, Prompt, LLMAnswer, Chunk
from ragtime.config import logger
import re
import json
import os
from datetime import datetime, timedelta
import asyncio
import requests
from typing import Dict, Any, ClassVar
from ragtime.retrievers import Retriever

SEARCH_USERNAME: str = "imad+ragtime@recital.ai"
SEARCH_PASSWORD: str = "Mido@123"
SEARCH_URL_LOGIN: str = "https://search.dev.auth.recital.ai/auth/api/v1/login/"
SEARCH_URL_SEARCH: str = "https://search.dev.api.recital.ai/search/api/v1/search/legacy"

class Search(Retriever):
    """
    LSA Retriever queries reciTAL Search
    """
    token: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3MjYxNDg2OTQuMDMwODEzLCJwcm9kdWN0cyI6WyJzZWFyY2giXSwidHlwZSI6ImFwaV90b2tlbiIsInByb2R1Y3QiOm51bGwsInVzZXJfaWQiOjU0LCJvcmdfaWQiOjE2LCJyb2xlIjoib3JnYWRtaW4iLCJpc19kYXRhc2NpZW50aXN0IjpmYWxzZSwiZ3JvdXBfaWRzIjpbXSwic2VydmljZSI6bnVsbH0.XMWquXqGXxhsGU2X50YZSgJ8uQrv8AhxtXG__1ImC5s"
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


MODEL_NAME = "AgentPublic/albertlight-7b"
API_URL = "https://albert.etalab.gouv.fr/api/v2"
TOKEN_DURATION = timedelta(hours=24)

class Albert_LLM(LLM):
    name: str = MODEL_NAME
    built_in_retriever: ClassVar[bool] = True
    _email = os.getenv("ALBERT_EMAIL")
    _username = os.getenv("ALBERT_USERNAME")
    _password = os.getenv("ALBERT_PASSWORD")
    _token = None
    _token_expiry = None
    _num_retries: int = 3
    _with_history: bool = False
    _chat_id: int = None

    def refresh_token(self):
        if self._token and self._token_expiry and datetime.now() < self._token_expiry:
            return

        data = {
            "email": self._email,
            "username": self._username,
            "password": self._password,
        }
        response = call_api(REQ_POST, f"{API_URL}/sign_in", json=data)
        self._token = response.json()["token"]
        self._token_expiry = datetime.now() + TOKEN_DURATION

    @property
    def headers(self):
        self.refresh_token()
        return {"Authorization": f"Bearer {self._token}"}

    def new_chat(self) -> int:
        data = {"chat_type": "qa"}
        response = call_api(REQ_POST, f"{API_URL}/chat", headers=self.headers, json=data)
        return response.json()["id"]

    def create_stream(self, query: str, limit: int = 7) -> int:
        data = {
            "query": query,
            "model_name": self.name,
            "mode": "rag",
            "with_history": self._with_history,
            "limit": limit,
        }
        
        if self._with_history:
            if not self._chat_id:
                self._chat_id = self.new_chat()
            url = f"{API_URL}/stream/chat/{self._chat_id}"
        else:
            url = f"{API_URL}/stream"
        
        response = call_api(REQ_POST, url, headers=self.headers, json=data)
        return response.json()["id"]

    def fetch_stream(self, stream_id: int) -> str:
        response = call_api(REQ_GET, f"{API_URL}/stream/{stream_id}/start", headers=self.headers, stream=True)

        answer = ""
        for line in response.iter_lines():
            if not line:
                continue

            decoded_line = line.decode("utf-8")
            _, _, data = decoded_line.partition("data: ")
            try:
                text = json.loads(data)
                if text == "[DONE]":
                    break
                answer += text
            except json.decoder.JSONDecodeError:
                print("\nDATA: " + data)
                print("\nERROR:")
                raise

        return answer

    def get_stream_data(self, stream_id: int):
        response = call_api(REQ_GET, f"{API_URL}/stream/{stream_id}", headers=self.headers)
        return response.json()

    def get_chunk_data(self, sheet_id: str):
        response = call_api(REQ_GET, f"{API_URL}/get_chunk/{sheet_id}", headers=self.headers)
        return response.json()

    async def complete(self, prompt: Prompt) -> LLMAnswer:
        retry: int = 1
        time_to_wait: float = 3.0
        result: str = ""
        while retry < self._num_retries:
            try :
                start_ts = datetime.now()
                
                stream_id = self.create_stream(query=prompt.user)
                result = self.fetch_stream(stream_id)
                
                stream_data = self.get_stream_data(stream_id)
                chunks = [self.get_chunk_data(sheet_id) for sheet_id in stream_data["rag_sources"]]
                break
            except Exception as e:
                await asyncio.sleep(time_to_wait)
                logger.debug(f"Excepton occured during api call, will retry 3 time each 3 second interval\nERROR:\n{e}")
                retry += 1
        duration = (datetime.now() - start_ts).total_seconds()
        return LLMAnswer(
            name=self.name,
            prompt=prompt,
            text=result,  # need refacto see albert doc,
            full_name=self.name,  # full name of the model?
            timestamp=start_ts,
            duration=duration,
            chunks=chunks
        )

        # return {
        #     "name": self.name,
        #     "prompt": prompt,
        #     "text": result,
        #     "full_name": self.name,
        #     "timestamp": start_ts,
        #     "duration": duration,
        #     "cost": 0.0,
        #     "stream_data": stream_data,
        #     "chunks": chunks
        # }
