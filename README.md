# Ragtime Project

This README provides instructions for setting up and customizing the Ragtime project, a framework for experimenting with and evaluating language models and retrieval systems.

## Getting Started

### Prerequisites

- Docker installed on your machine
- Git

### Installation and Launching

1. Clone the repository:

   ```
   git clone https://github.com/recitalAI/ragtime.git
   ```

2. Navigate to the project directory:

   ```
   cd ragtime
   ```

3. Build the Docker container:

   ```
   docker compose build
   ```

4. Launch the container (this will automatically start the servers):

   ```
   docker compose up
   ```

   Note: If you encounter an error about logs on the first run, simply relaunch the container and it should work.

## Customization

You can customize the retriever and the LLMs you want to use in the `classes.py` file. The custom classes you create will appear in the UI for selection.

### Customizing the LLM

To create a custom LLM, follow these steps:

1. Open `classes.py`

2. Import necessary modules:

   ```python
   from ragtime.llms import LLM
   from ragtime.expe import Prompt, LLMAnswer
   from ragtime.config import logger
   from datetime import datetime
   import asyncio
   ```

3. Create a new class that inherits from `LLM`:

   ```python
   class MyCustomLLM(LLM):
       name: str = "MyCustomModel"
       built_in_retriever: ClassVar[bool] = False  # Set to True if using API-based retrieval

       async def complete(self, prompt: Prompt) -> LLMAnswer:
           # Your implementation here
           pass
   ```

4. Implement the `complete` method with your custom logic. The `complete` method should return an `LLMAnswer` object with the following structure:

   ```python
   return LLMAnswer(
       name=self.name,
       prompt=prompt,
       text=result,
       full_name=self.name,
       timestamp=start_ts,
       duration=duration,
       chunks=chunks  # Optional, include if you're using retrieval
   )
   ```

Example of a custom LLM implementation:

```python
class MyCustomLLM(LLM):
    name: str = "MyCustomModel"
    built_in_retriever: ClassVar[bool] = False
    _num_retries: int = 3

    async def complete(self, prompt: Prompt) -> LLMAnswer:
        retry: int = 1
        time_to_wait: float = 3.0
        result: str = ""
        while retry < self._num_retries:
            try:
                start_ts = datetime.now()

                # Your custom API calls or processing logic here
                stream_id = self.create_stream(query=prompt.user)
                result = self.fetch_stream(stream_id)

                stream_data = self.get_stream_data(stream_id)
                chunks = [self.get_chunk_data(sheet_id) for sheet_id in stream_data["rag_sources"]]
                break
            except Exception as e:
                await asyncio.sleep(time_to_wait)
                logger.debug(f"Exception occurred during API call, will retry. Error: {e}")
                retry += 1

        duration = (datetime.now() - start_ts).total_seconds()
        return LLMAnswer(
            name=self.name,
            prompt=prompt,
            text=result,
            full_name=self.name,
            timestamp=start_ts,
            duration=duration,
            chunks=chunks
        )

```

Key points to remember:

- The `complete` method should handle retries and exceptions.
- Always return an `LLMAnswer` object with the required fields.
- Include `chunks` in the `LLMAnswer` if your LLM performs retrieval.
- Use `logger.debug` for logging important information or errors.
- Implement any additional methods needed for your custom LLM's functionality.

### Customizing the Retriever

To create a custom Retriever, follow these steps:

1. Open `classes.py`

2. Import necessary modules:

   ```python
   from ragtime.retrievers import Retriever
   from ragtime.expe import QA, Chunk
   from ragtime.config import logger
   ```

3. Create a new class that inherits from `Retriever`:

   ```python
   class MyCustomRetriever(Retriever):
       def retrieve(self, qa: QA):
           # Your implementation here
           pass
   ```

4. Implement the `retrieve` method with your custom logic.

Example of a custom Retriever implementation:

```python
import requests
from datetime import datetime
from typing import Dict, Any

class MyCustomRetriever(Retriever):
    token: str = "your_default_token_here"
    token_last_update: datetime = None
    TOKEN_DURATION: int = 1  # max token duration in hours

    def retrieve(self, qa: QA):
        logger.debug('Start Custom Retriever')
        self._refresh_token()
        qa.chunks.empty()

        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token}"
        }

        params: Dict[str, Any] = {
            "query": qa.question.text
        }

        try:
            response = requests.post("YOUR_API_ENDPOINT", headers=headers, params=params, json={})
            response.raise_for_status()
            search_results = response.json()

            for i, search_chunk in enumerate(search_results.get("chunks", [])):
                chunk = Chunk()
                # Process and populate chunk data
                # ...
                qa.chunks.append(chunk)

            logger.debug(f'Retrieved {len(qa.chunks)} chunk(s)')

        except Exception as e:
            logger.error(f"Error in retrieve method: {str(e)}")

    def _refresh_token(self):
        # Implement token refresh logic
        pass
```

## UI Integration

- Custom LLMs will appear in the "CUSTOMIZED" section of the LLM configuration when starting an experiment.
- Custom Retrievers will show up in the Retriever configuration selection section.

## Best Practices

1. **Validate Custom Classes**: Before integrating your custom LLM or Retriever, validate the classes to ensure they work correctly and meet all required interfaces.

2. **API Key Management**: Store API keys and sensitive information in environment variables or secure configuration interface.

3. **Rate Limiting**: If your custom LLM or Retriever interacts with external APIs, implement rate limiting to avoid exceeding usage quotas.

## Notes

- The Retriever should be a child class of `Retriever`
- The LLM should be a child class of `LLM`
- Set `built_in_retriever` to `True` in your custom LLM class if the retrieving step is done on the server-side via API calls.
