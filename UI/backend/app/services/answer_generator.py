"""Answer generation. Built per request/job with the target models — no
shared singleton state (B3 fix): two overlapping requests can no longer
swap each other's models mid-run.
"""
import logging
from typing import List, Union

from ragtime.expe import QA, Expe, Question
from ragtime.generators import AnsGenerator
from ragtime.llms import LiteLLM, ReasoningLLM
from ragtime.prompters import AnsPrompterBase, AnsPrompterWithRetrieverFR

from app.infra.event_loop import ensure_event_loop
from app.utils.class_detector import get_llm_classes, get_retriever_classes
from app.services.model_meta import reasoning_meta_for


class AnswerGeneratorService:
    def __init__(self, models: Union[str, List[str]], use_retriever: bool = False, retriever_type: str = None, reasoning: bool = None, reasoning_effort: str = None):
        self.models = [models] if isinstance(models, str) else models
        self.llms = []

        retriever = None
        retriever_classes = get_retriever_classes()
        llm_classes = get_llm_classes()
        for model in self.models:
            llm_class = next((cls for cls in llm_classes if cls.__name__ == model), None)

            if use_retriever and retriever_type:
                retriever_class = next((cls for cls in retriever_classes if cls.__name__ == retriever_type), None)
                if retriever_class:
                    if llm_class and getattr(llm_class, 'built_in_retriever', True):
                        retriever = None
                    else:
                        retriever = retriever_class()
                else:
                    logging.warning(f"No retriever class found for type: {retriever_type}")

            if llm_class:
                prompter = AnsPrompterBase() if getattr(llm_class, 'built_in_retriever', True) else (AnsPrompterWithRetrieverFR() if use_retriever else AnsPrompterBase())
                kwargs = {}
                if issubclass(llm_class, ReasoningLLM):
                    if reasoning is not None:
                        kwargs['reasoning'] = reasoning
                    # Effort ('low'|'medium'|'high') only for reasoning models;
                    # ignored elsewhere. The package sends it to litellm when set.
                    if reasoning_effort:
                        kwargs['reasoning_effort'] = reasoning_effort
                self.llms.append(llm_class(prompter=prompter, **kwargs))
            else:
                prompter = AnsPrompterWithRetrieverFR() if use_retriever else AnsPrompterBase()
                meta = reasoning_meta_for(model)
                if meta:
                    # Catalog marks this string model as a reasoning model:
                    # build a ReasoningLLM so its thinking is captured cleanly
                    # (and its toggle, when supported, actually reaches litellm).
                    rk = {'prompter': prompter, 'name': model}
                    if meta.get('toggle_style'):
                        rk['reasoning_toggle_style'] = meta['toggle_style']
                        if reasoning is not None:
                            rk['reasoning'] = reasoning
                    if reasoning_effort:
                        rk['reasoning_effort'] = reasoning_effort
                    self.llms.append(ReasoningLLM(**rk))
                else:
                    self.llms.append(LiteLLM(name=model, prompter=prompter))

        self.answer_generator = AnsGenerator(llms=self.llms, retriever=retriever)

    def generate_answers(self, expe: Expe) -> Expe:
        ensure_event_loop()
        self.answer_generator.generate(expe=expe)
        return expe

    def generate_answer_for_question(self, question_data: dict) -> dict:
        expe = Expe()
        qa = QA(question=Question(text=question_data['text']))
        expe.append(qa)
        updated_expe = self.generate_answers(expe)
        return updated_expe[0].model_dump()
