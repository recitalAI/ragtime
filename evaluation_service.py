from ragtime.expe import Expe, StartFrom, Eval, Answer
from ragtime.generators import EvalGenerator, EvalGeneratorChunks
from ragtime.prompters import EvalPrompterChunks, EvalPrompterFRV2
from ragtime.llms import LLM, LiteLLM
import os
import logging

class EvaluationService:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.answer_prompter = EvalPrompterFRV2()
        self.chunk_prompter = EvalPrompterChunks()
        self.model = None

    def set_model(self, model_name: str):
        self.model = model_name

    def evaluate_answers(self, expe: Expe) -> Expe:
        if not self.model:
            raise ValueError("Model not set. Call set_model() before evaluating.")
        eval_gen = EvalGenerator(llms=self.model, prompter=self.answer_prompter)
        eval_gen.generate(expe=expe)
        return expe

    def evaluate_chunks(self, expe: Expe) -> Expe:
        if not self.model:
            raise ValueError("Model not set. Call set_model() before evaluating.")
        
        # Initialize metadata for all answers before evaluation
        self._initialize_metadata(expe)
        
        chunk_eval_gen = EvalGeneratorChunks(llms=self.model, prompter=self.chunk_prompter)
        
        try:
            chunk_eval_gen.generate(expe=expe)
        except Exception as e:
            logging.error(f"Error in evaluate_chunks: {str(e)}")
            # If an error occurs during generation, we'll log it and return the expe as is
            # This allows the experiment to continue and save partial results
        
        return expe

    def _initialize_metadata(self, expe: Expe):
        for qa in expe:
            for ans in qa.answers:
                if not isinstance(ans, Answer):
                    continue
                if not hasattr(ans, 'eval') or ans.eval is None:
                    ans.eval = Eval()
                if not hasattr(ans.eval, 'meta') or ans.eval.meta is None:
                    ans.eval.meta = {}
                
                # Initialize all required metadata fields
                meta = ans.eval.meta
                meta.setdefault('missing', [])
                meta.setdefault('nb_missing', 0)
                meta.setdefault('ok', [])
                meta.setdefault('nb_ok', 0)
                meta.setdefault('hallu', [])
                meta.setdefault('nb_hallu', 0)