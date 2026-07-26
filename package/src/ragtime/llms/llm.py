from abc import abstractmethod

from ragtime.prompters.prompter import Prompter

from ragtime.base import RagtimeBase
from ragtime.expe import QA, Prompt, LLMAnswer, WithLLMAnswer, StartFrom, Chunk
from ragtime.config import logger, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE

import litellm
from litellm import completion_cost, acompletion
from litellm.exceptions import RateLimitError
import re

from datetime import datetime
from typing import Optional, Any
import asyncio

# Drop provider-unsupported params instead of 400-ing (reasoning models reject
# temperature!=1 and max_tokens). Set once at import time.
litellm.drop_params = True


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
        assert not prev_obj or (cur_obj.__class__ == prev_obj.__class__)
        cur_class_name: str = cur_obj.__class__.__name__
        original_logger_prefix: str = logger.prefix

        # Get prompt
        logger.prefix += f"[{self.prompter.__class__.__name__}]"

        if not (prev_obj and prev_obj.llm_answer and prev_obj.llm_answer.prompt) \
                or (start_from <= StartFrom.prompt and not b_missing_only):
            logger.debug(f"Generate prompt")
            prompt = self.prompter.get_prompt(**kwargs)
        else:
            logger.debug(f"Reuse existing Prompt")
            prompt = prev_obj.llm_answer.prompt

        logger.prefix = original_logger_prefix

        # Generates text
        result: WithLLMAnswer = cur_obj
        if not (prev_obj and prev_obj.llm_answer) or (start_from <= StartFrom.llm and not b_missing_only):
            original_logger_prefix: str = logger.prefix
            logger.prefix += f'[{self.name}]'
            logger.debug(f'Generate LLMAnswer with "{self.name}"')            
            b_exception:bool = False
            exc:Exception = None
            try:
                result.llm_answer = await self.complete(prompt)
                if result.llm_answer:
                    if result.llm_answer.chunks:
                        for chunk in result.llm_answer.chunks:
                            meta = {k: v for k, v in chunk.items() if k != 'text'}
                            chunk_ = Chunk(meta=meta, text=chunk['text'])
                            qa.chunks.append(chunk_)
                    result.llm_answer.prompt = prompt  # updates the prompt
                    result.llm_answer.prompt.prompter = self.prompter.name  # and it name
                else:
                    b_exception = True
            except Exception as e:
                exc = e
                b_exception = True

            if b_exception:
                logger.exception(f"Exception while generating - skip it\n{exc if exc else ''}")
                return None
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
            try:
                self.prompter.post_process(qa=qa, cur_obj=result)
            except Exception as e:
                logger.exception(f'Error while post-processing\n{e}')
        else:
            logger.debug("Reuse post-processing")

        logger.prefix = original_logger_prefix

        return result

    @abstractmethod
    async def complete(self, prompt: Prompt) -> LLMAnswer:
        raise NotImplementedError("Must implement this!")


class LiteLLM(LLM):
    """
    A LiteLLM must be provided with a Prompter and a name at creation time
    Simple extension of LLM based on the litellm library.
    Allows to call LLMs by their name in a stantardized way.
    The default get_prompt method is not changed.
    The generate method uses the standard litellm completion method.
    Default values of temperature (0.0)
    Number of retries when calling the API (3) can be changed.
    The proper API keys and endpoints have to be specified in the keys.py module.
    """

    name: str
    temperature: float = DEFAULT_TEMPERATURE
    num_retries: int = 3
    # Extra kwargs merged into every completion call, e.g.
    # {"api_base": ..., "api_key": ...} to reach an OpenAI-compatible
    # endpoint such as OVH AI Endpoints.
    extra_params: dict = {}

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
                    reasonning_effort=None,
                    **self.extra_params,
                )
                break
            except RateLimitError as e:
                logger.debug(f"Rate limit reached - will retry in {time_to_wait:.2f}s\n\t{str(e)}")
                await asyncio.sleep(time_to_wait)
                retry += 1
            except Exception as e:
                logger.exception(f'The following exception occurred with prompt\n"{str(prompt)[:300]}"\nException: {e}')
                return None

        try:
            full_name: str = answer["model"]
            text: str = answer["choices"][0]["message"]["content"]
            duration: float = (answer._response_ms /1000 if hasattr(answer, "_response_ms") else None)  # sometimes _response_ms is not present
            # Cost must never discard a good answer: models with no LiteLLM
            # price map (e.g. OVH classic models) raise here.
            try:
                cost: float = float(completion_cost(answer))
            except Exception as cost_err:
                logger.debug(f"completion_cost unavailable for {self.name}: {cost_err}")
                cost = 0.0
            return LLMAnswer(
                name=self.name,
                full_name=full_name,
                text=text,
                timestamp=start_ts,
                duration=duration,
                cost=cost,
            )
        except Exception as e:
            logger.debug(f"Failed to process the Answer.\n{e}")
        return LLMAnswer()


# ---------------------------------------------------------------------------
# Reasoning models
# ---------------------------------------------------------------------------
# Reasoning ("thinking") models emit a chain-of-thought that must NOT reach the
# prompters' post_process(), which parse llm_answer.text directly (json.loads
# for answers, line-split for facts, OK/HALLU regex for eval). If the thinking
# text lands in .text, every one of those parsers silently corrupts -> the
# "No Answers"/garbage-facts symptom.
#
# Where the thinking goes depends on the serving stack:
#   * OpenAI o-series / gpt-5, Anthropic thinking, and any vLLM deployment with
#     a reasoning parser (OVH gpt-oss "Harmony" analysis channel, OVH Qwen3)
#     put the final answer in message.content and the thinking in a SEPARATE
#     field (reasoning_content / thinking_blocks). -> ReasoningLLM is enough.
#   * Raw DeepSeek-R1-style models leak <think>...</think> INTO content.
#     -> ThinkTagReasoningLLM additionally strips it.
#
# All classes here only override how the raw response is turned into an
# LLMAnswer; get_prompt and the prompters are untouched.


class ReasoningLLM(LiteLLM):
    """LiteLLM for models whose reasoning is returned in a separate field
    (reasoning_content / thinking_blocks), leaving message.content clean.

    - reasoning: user-facing toggle. None = provider default; True/False sent
      to models that support switching (Anthropic thinking, Qwen3
      enable_thinking). Ignored by models that can't be toggled.
    - reasoning_effort: 'low'|'medium'|'high' for models that accept it
      (o-series, gpt-5, gpt-oss). None = not sent.
    - The thinking text, when present, is preserved in
      llm_answer.meta['reasoning_content'] so nothing is lost.
    """

    reasoning: Optional[bool] = None
    reasoning_effort: Optional[str] = None

    # How this model accepts a reasoning on/off toggle:
    #   'anthropic'      -> `thinking` param (Anthropic extended thinking)
    #   'chat_template'  -> extra_body.chat_template_kwargs.enable_thinking
    #                       (vLLM servers that opt in; NOT generic OVH today)
    #   None             -> no per-request toggle; reasoning is fixed
    # Subclasses set this. Default None means we never send a toggle param the
    # endpoint might reject (which is what broke OVH Qwen3: OVH does not yet
    # accept chat_template_kwargs).
    reasoning_toggle_style: Optional[str] = None

    # Reasoning models spend the SAME token budget on their hidden thinking and
    # on the visible answer. With the package default (max_tokens=2000, sized
    # for visible text only) a model can burn the whole budget reasoning and
    # return EMPTY content with finish_reason='length' -- the answer is then
    # dropped by AnsGenerator ("if ans and ans.text"), which looks like
    # "No Answers" for that question while others succeed. Documented by
    # OpenAI: max_completion_tokens includes reasoning tokens.
    # We therefore raise the cap for reasoning models.
    reasoning_token_budget: int = 16000

    def _effective_max_tokens(self) -> int:
        base = self.max_tokens or 0
        return max(base, self.reasoning_token_budget)

    def _completion_kwargs(self) -> dict:
        kwargs: dict = dict(self.extra_params)
        if self.reasoning_effort:
            kwargs["reasoning_effort"] = self.reasoning_effort
        if self.reasoning is not None and self.reasoning_toggle_style:
            if self.reasoning_toggle_style == "anthropic":
                kwargs["thinking"] = {
                    "type": "enabled" if self.reasoning else "disabled"
                }
            elif self.reasoning_toggle_style == "chat_template":
                kwargs.setdefault("extra_body", {})["chat_template_kwargs"] = {
                    "enable_thinking": bool(self.reasoning)
                }
        return kwargs

    def _extract_text(self, message: Any) -> str:
        """Return the clean answer text. Base implementation trusts content."""
        return message.get("content") or ""

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
                answer = await acompletion(
                    messages=messages,
                    model=self.name,
                    temperature=self.temperature,
                    num_retries=self.num_retries,
                    max_tokens=self._effective_max_tokens(),
                    **self._completion_kwargs(),
                )
                break
            except RateLimitError as e:
                logger.debug(f"Rate limit reached - will retry in {wait_step:.2f}s\n\t{str(e)}")
                await asyncio.sleep(wait_step)
                retry += 1
            except Exception as e:
                logger.exception(f'The following exception occurred with prompt\n"{str(prompt)[:300]}"\nException: {e}')
                return None

        try:
            full_name: str = answer["model"]
            message = answer["choices"][0]["message"]
            text: str = self._extract_text(message)
            if not (text or "").strip():
                # Empty visible answer: almost always the reasoning budget was
                # exhausted (finish_reason 'length'). Surface it instead of
                # silently yielding an answer-less question.
                finish = None
                try:
                    finish = answer["choices"][0].get("finish_reason")
                except Exception:
                    pass
                logger.error(
                    f"{self.name} returned EMPTY content (finish_reason={finish}). "
                    f"The reasoning budget ({self._effective_max_tokens()} tokens) was likely "
                    f"consumed by hidden reasoning; raise reasoning_token_budget or lower reasoning_effort."
                )
            duration: float = (answer._response_ms / 1000 if hasattr(answer, "_response_ms") else None)
            # Cost must never sink a good answer: models with no LiteLLM price
            # map (e.g. OVH Qwen3-32B -> "This model isn't mapped yet") raise
            # here. Isolate it and default to 0 so the answer is kept.
            try:
                cost: float = float(completion_cost(answer))
            except Exception as cost_err:
                logger.debug(f"completion_cost unavailable for {self.name}: {cost_err}")
                cost = 0.0
            llm_answer = LLMAnswer(
                name=self.name,
                full_name=full_name,
                text=text,
                timestamp=start_ts,
                duration=duration,
                cost=cost,
            )
            # Preserve the thinking so nothing is lost and results can show it.
            reasoning_txt = message.get("reasoning_content") if hasattr(message, "get") else None
            if reasoning_txt:
                llm_answer.meta["reasoning_content"] = reasoning_txt
            return llm_answer
        except Exception as e:
            logger.debug(f"Failed to process the Answer.\n{e}")
        return LLMAnswer()


# Matches a leading <think>...</think> block, or a tag-less "...</think>"
# prefix (some vLLM/Google deployments omit the opening tag).
_THINK_RE = re.compile(r"^\s*(?:<think>)?.*?</think>\s*", re.DOTALL)


class ThinkTagReasoningLLM(ReasoningLLM):
    """For models that leak their reasoning as <think>...</think> INSIDE
    message.content (raw DeepSeek-R1-style). Strips the block from the answer
    and keeps it in meta. Not required by the current OVH roster (OVH serves
    gpt-oss/Qwen3 through vLLM reasoning parsers), but kept for models added
    later that behave this way."""

    def _extract_text(self, message: Any) -> str:
        content: str = (message.get("content") or "") if hasattr(message, "get") else ""
        stripped = _THINK_RE.sub("", content, count=1)
        return stripped if stripped else content
