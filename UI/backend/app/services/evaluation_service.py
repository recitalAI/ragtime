"""Answer/chunk evaluation. Built per request/job with the judge model —
no shared singleton state (B3 fix).
"""
import logging

from ragtime.expe import Answer, Eval, Expe
from ragtime.generators import EvalGenerator, EvalGeneratorChunks

from app.services.llm_factory import build_llm
from ragtime.prompters import EvalPrompterChunks, EvalPrompterFRV2

from app.infra.event_loop import ensure_event_loop


class EvaluationService:
    def __init__(self, model_name: str):
        self.answer_prompter = EvalPrompterFRV2()
        self.chunk_prompter = EvalPrompterChunks()
        self.model = model_name

    def evaluate_answers(self, expe: Expe) -> Expe:
        ensure_event_loop()
        # Pass an LLM OBJECT, not a bare string: the package would wrap a
        # string in a plain LiteLLM, which for a reasoning judge (o4-mini,
        # gpt-5) means the 2000-token budget is consumed by hidden reasoning
        # and the verdict text comes back EMPTY -> every fact scored missing.
        eval_gen = EvalGenerator(llms=[build_llm(self.model, self.answer_prompter)],
                                 prompter=self.answer_prompter)
        eval_gen.generate(expe=expe)
        return expe

    def evaluate_chunks(self, expe: Expe) -> Expe:
        ensure_event_loop()
        # Initialize metadata for all answers before evaluation
        self._initialize_metadata(expe)

        chunk_eval_gen = EvalGeneratorChunks(llms=[build_llm(self.model, self.chunk_prompter)],
                                             prompter=self.chunk_prompter)

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
