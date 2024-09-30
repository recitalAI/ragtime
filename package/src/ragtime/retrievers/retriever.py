#!/usr/bin/env python3

from abc import abstractmethod
from ragtime.base import RagtimeBase
from ragtime.expe import QA


class Retriever(RagtimeBase):
    """
    Retriever abstract class
    The `retrieve` method must be implemented
    The LLM must be given as a list of string from https://litellm.vercel.app/docs/providers
    """

    @abstractmethod
    def retrieve(self, qa: QA):
        """
        Retrurns the Chunks from a Question and writes them in the QA object
        """
        raise NotImplementedError("Must implement this!")
