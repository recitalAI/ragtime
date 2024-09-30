import os
from ragtime.expe import Expe, QA, Question, Answer, Chunks, Chunk
from ragtime.generators import AnsGenerator
from ragtime.prompters import AnsPrompterBase, AnsPrompterWithRetrieverFR, Prompter
from ragtime.llms import LiteLLM
from typing import List, Union
from app.utils.class_detector import get_retriever_classes, get_llm_classes
import logging



class AnswerGeneratorService:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.answer_generator = None

    def set_model(self, models: Union[str, List[str]], use_retriever: bool = False, retriever_type: str = None):

        self.models = [models] if isinstance(models, str) else models
        self.llms = []

        retriever = None
        retriever_classes = get_retriever_classes()
        llm_classes = get_llm_classes()

        if use_retriever and retriever_type:
            retriever_class = next((cls for cls in retriever_classes if cls.__name__ == retriever_type), None)
            if retriever_class:
                retriever = retriever_class()
            else:
                logging.warning(f"No retriever class found for type: {retriever_type}")

        for model in self.models:
            llm_class = next((cls for cls in llm_classes if cls.__name__ == model), None)
            if llm_class:
                prompter = AnsPrompterBase() if getattr(llm_class, 'built_in_retriever', False) else (AnsPrompterWithRetrieverFR() if use_retriever else AnsPrompterBase())
                self.llms.append(llm_class(prompter=prompter))
            else:
                prompter = AnsPrompterWithRetrieverFR() if use_retriever else AnsPrompterBase()
                self.llms.append(LiteLLM(name=model, prompter=prompter))

        self.answer_generator = AnsGenerator(llms=self.llms, retriever=retriever)

    def generate_answers(self, expe: Expe) -> Expe:
        self.answer_generator.generate(expe=expe)
        return expe

    def generate_answer_for_question(self, question_data: dict) -> dict:
        expe = Expe()
        qa = QA(question=Question(text=question_data['text']))
        expe.append(qa)
        updated_expe = self.generate_answers(expe)
        return updated_expe[0].model_dump()
