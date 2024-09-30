#!/usr/bin/env python3

from abc import abstractmethod, ABC

from ragtime.base import RagtimeBase
from ragtime.expe import StartFrom, QA
from ragtime.llms import LLM, LiteLLM
from ragtime.prompters.prompter import Prompter
from ragtime.base import RagtimeException
from ragtime.config import logger
from ragtime.expe import Expe

import time
from typing import Optional
import asyncio


class TextGenerator(RagtimeBase, ABC):
    """
    Abstract class for QuestionGenerator, AnswerGenerator, FactGenerator, EvalGenerator
    """

    llms: Optional[list[LLM]] = []
    b_use_chunks: bool = False
    wait_between_calls:int = 0

    def __init__(self, llms: list = None, prompter:Prompter = None, wait_between_calls:int = 0):
        """
        Args
            llms(LLM or list[LLM]) : list of LLM objects
        """
        super().__init__()
        if not llms:
            raise RagtimeException("llms list is empty! Please provide at least one.")
        if isinstance(llms, str):
            llms = [llms]
        for llm in llms:
            if isinstance(llm, str):
                if prompter:
                    self.llms.append(LiteLLM(name=llm, prompter=prompter))
                else:
                    raise RagtimeException('You must provide a Prompter to create LLMs from their names only')
            elif isinstance(llm, LLM):
                self.llms.append(llm)
            else:
                raise RagtimeException(f'Objects in the llms list must be either str or LLM - {llm} is not')
        self.wait_between_calls = wait_between_calls

    @property
    def llm(self) -> LLM:
        """
        Helper function to get the first LLM when only one is provided (like for EvalGenerator and FactGenerator)
        """
        if not self.llms:
            return None
        return self.llms[0]

    def generate(
        self,
        expe: Expe,
        save_every: int = 0,
        b_missing_only: bool = False,
        only_llms: list[str] = None,
        start_from: StartFrom = StartFrom.beginning,
    ):
        """
        Main method calling "gen_for_qa" for each QA in an Expe. Returns False if completed with error, True otherwise
        The main step in generation are :
        - beginning: start of the process - when start_from=beginning, the whole process is executed
            - chunks: only for Answer generation - chunk retrieval, if a Retriever is associated with the Answer Generator object
        Takes a Question and returns the Chunks
        - prompt: prompt generation, either directly using the question or with the chunks if any
        Takes a Question + optional Chunks and return a Prompt
        - llm: calling the LLM(s) with the generated prompts
        Takes a Prompt and return a LLMAnswer
        - post_process: post-processing the aswer returned by the LLM(s)
        Takes LLMAnswer + other information and updates the Answer object
        Args:
            - expe: Expe object to generate for
            - start_from: allows to start generation from a specific step in the process
            - b_missing_only: True to execute the steps only when the value is absent, False to execute everything
            even if a value already exists
            - only_llms: restrict the llms to be computed again - used in conjunction with start_from -
            if start from beginning, chunks or prompts, compute prompts and llm answers for the list only -
            if start from llm, recompute llm answers for these llm only - has not effect if start
        """

        nb_q: int = len(expe)

        async def _generate_for_qa(num_q: int, qa: QA):
            logger.prefix = f"[{self.__class__.__name__}][{num_q}/{nb_q}]"
            logger.info(f'*** Question "{qa.question.text}"')
            try:
                await self.gen_for_qa(
                    qa=qa,
                    start_from=start_from,
                    b_missing_only=b_missing_only,
                    only_llms=only_llms,
                )
            except Exception as e:
                logger.exception(f"Exception caught - saving what has been done so far:\n{e}")
                expe.save_to_json()
                expe.save_temp(name=f"Stopped_at_{num_q}_of_{nb_q}_")
                return
            time.sleep(self.wait_between_calls)
            logger.info(f'End question "{qa.question.text}"')

            if save_every and (num_q % save_every == 0):
                expe.save_to_json()

        original_logger_prefix:str = logger.prefix
        loop = asyncio.get_event_loop()
        tasks = [_generate_for_qa(num_q, qa) for num_q, qa in enumerate(expe, start=1)]
        logger.info(f"{len(tasks)} tasks created")
        loop.run_until_complete(asyncio.gather(*tasks))
        logger.prefix = original_logger_prefix

    def write_chunks(self, qa: QA):
        """Write chunks in the current qa if a Retriever has been given when creating the object. Ignore otherwise"""
        raise NotImplementedError("Must implement this if you want to use it!")

    @abstractmethod
    async def gen_for_qa(
        self,
        qa: QA,
        start_from: StartFrom = StartFrom.beginning,
        b_missing_only: bool = True,
        only_llms: list[str] = None,
    ):
        """
        Method to be implemented to generate Answer, Fact and Eval
        """
        raise NotImplementedError("Must implement this!")
