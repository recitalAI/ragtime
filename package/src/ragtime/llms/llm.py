from abc import abstractmethod

from ragtime.prompters.prompter import Prompter

from ragtime.base import RagtimeBase
from ragtime.expe import QA, Prompt, LLMAnswer, WithLLMAnswer, StartFrom, Chunk
from ragtime.config import logger, DEFAULT_MAX_TOKENS

from litellm import completion_cost, acompletion
from litellm.exceptions import RateLimitError

from datetime import datetime
from typing import Optional
import asyncio


class LLM(RagtimeBase):
    """
    Base class for text to text LLMs.
    Class deriving from LLM must implement `complete`.
    A Prompter must be provided at creation time.
    Instantiates a get_prompt so as to be able change the prompt LLM-wise.
    """

    name: Optional[str] = None
    prompter: Prompter
    max_tokens: int = DEFAULT_MAX_TOKENS
    # _semaphore: asyncio.Semaphore = asyncio.Semaphore(1)

    async def generate(
        self,
        cur_obj: WithLLMAnswer,
        prev_obj: WithLLMAnswer,
        qa: QA,
        start_from: StartFrom,
        b_missing_only: bool,
        **kwargs,
    ) -> WithLLMAnswer:
        """
        Generate prompt and execute LLM
        Returns the retrieved or created object containing the LLMAnswer
        If None, LLMAnswer retrieval or generation went wrong and post-processing
        must be skipped
        """
        # await self._semaphore.acquire()
        # logger.prefix = f"[{self.name}]"

        assert not prev_obj or (cur_obj.__class__ == prev_obj.__class__)
        cur_class_name: str = cur_obj.__class__.__name__
        original_logger_prefix: str = logger.prefix

        # Get prompt

        logger.prefix += f"[{self.prompter.__class__.__name__}]"

        if not (prev_obj and prev_obj.llm_answer and prev_obj.llm_answer.prompt) \
                or (start_from <= StartFrom.prompt and not b_missing_only):
            # logger.debug(f"Either no {cur_class_name} / LLMAnswer / Prompt exists yet, or you asked to regenerate Prompt ==> generate prompt")
            logger.debug(f"Generate prompt")
            prompt = self.prompter.get_prompt(**kwargs)
        else:
            logger.debug(f"Reuse existing Prompt")
            prompt = prev_obj.llm_answer.prompt

        logger.prefix = original_logger_prefix

        # Generates text
        result: WithLLMAnswer = cur_obj
        if not (prev_obj and prev_obj.llm_answer) or (start_from <= StartFrom.llm and not b_missing_only):
            # logger.debug(f"Either no {cur_class_name} / LLMAnswer exists yet, or you asked to regenerate it ==> generate LLMAnswer")
            original_logger_prefix: str = logger.prefix
            logger.prefix += f'[{self.name}]'
            logger.debug(f'Generate LLMAnswer with "{self.name}"')
            try:
                result.llm_answer = await self.complete(prompt)
                if result.llm_answer.chunks:
                    for chunk in result.llm_answer.chunks:
                        meta = {k: v for k, v in chunk.items() if k != 'text'}
                        chunk_ = Chunk(meta=meta, text=chunk['text'])
                        qa.chunks.append(chunk_)
                result.llm_answer.prompt = prompt  # updates the prompt
                result.llm_answer.prompt.prompter = self.prompter.name  # and it name
            except Exception as e:
                logger.exception(f"Exception while generating - skip it\n{e}")
                result = None
        else:
            logger.debug(f"Reuse existing LLMAnswer in {cur_class_name}")
            result = prev_obj

        # Post-process
        logger.prefix = original_logger_prefix
        logger.prefix += f"[{self.prompter.__class__.__name__}]"

        if result.llm_answer and (
            not (prev_obj and prev_obj.llm_answer)
            or not b_missing_only
            and start_from <= StartFrom.post_process
        ):
            logger.debug(f"Post-process {cur_class_name}")
            self.prompter.post_process(qa=qa, cur_obj=result)
        else:
            logger.debug("Reuse post-processing")

        logger.prefix = original_logger_prefix

        return result

    @abstractmethod
    async def complete(self, prompt: Prompt) -> LLMAnswer:
        raise NotImplementedError("Must implement this!")


class LiteLLM(LLM):
    """
    Simple extension of LLM based on the litellm library.
    Allows to call LLMs by their name in a stantardized way.
    The default get_prompt method is not changed.
    The generate method uses the standard litellm completion method.
    Default values of temperature (0.0)
    Number of retries when calling the API (3) can be changed.
    The proper API keys and endpoints have to be specified in the keys.py module.
    """

    name: str
    temperature: float = 0.0
    num_retries: int = 3

    async def complete(self, prompt: Prompt) -> LLMAnswer:
        messages: list[dict] = [
            {"content": prompt.system, "role": "system"},
            {"content": prompt.user, "role": "user"},
        ]
        retry: int = 1
        wait_step: float = 3.0
        start_ts: datetime = datetime.now()
        answer: dict = None
        while retry < self.num_retries:
            try:
                time_to_wait: float = wait_step
                answer = await acompletion(
                    messages=messages,
                    model=self.name,
                    temperature=self.temperature,
                    num_retries=self.num_retries,
                    max_tokens=self.max_tokens,
                )
                break
            except RateLimitError as e:
                logger.debug(f"Rate limit reached - will retry in {time_to_wait:.2f}s\n\t{str(e)}")
                await asyncio.sleep(time_to_wait)
                retry += 1
            except Exception as e:
                logger.exception(
                    f"The following exception occurred with prompt {prompt}"
                    + "\n"
                    + str(e)
                )
                return None

        try:
            full_name: str = answer["model"]
            text: str = answer["choices"][0]["message"]["content"]
            duration: float = (answer._response_ms /1000 if hasattr(answer, "_response_ms") else None)  # sometimes _response_ms is not present
            cost: float = float(completion_cost(answer))
            return LLMAnswer(
                name=self.name,
                full_name=full_name,
                text=text,
                timestamp=start_ts,
                duration=duration,
                cost=cost,
            )
        except Exception as e:
            logger.debug(f"Faile to process the Answer. {e}")
        return LLMAnswer()
