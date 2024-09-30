from abc import ABC, abstractmethod
from ragtime.base import RagtimeBase
from ragtime.expe import Prompt, QA, WithLLMAnswer


class Prompter(RagtimeBase, ABC):
    """
    Base Prompter class. Every Prompter must inherit from it.
    A Prompter is designed to generate prompts for Answers, Facts and Evals.
    It also contains a method to post-process text returned by an LLM, since post-processing is directly related to the prompt
    It must be provided to every LLM objects at creation time
    """
    system:str = ""
    name:str = ""
    
    def __init__(self):
        super().__init__()
        self.name = self.__class__.__name__

    @abstractmethod
    def get_prompt(self) -> Prompt:
        raise NotImplementedError("Must implement this!")

    @abstractmethod
    def post_process(self, qa: QA, cur_obj: WithLLMAnswer) -> WithLLMAnswer:
        raise NotImplementedError("Must implement this!")
