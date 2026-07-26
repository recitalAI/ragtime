"""Fact generation. Built per request with the target model — no shared
singleton state (B3 fix).
"""
import logging

from ragtime.expe import Expe
from ragtime.generators import FactGenerator
from ragtime.llms import LiteLLM

from app.services.llm_factory import build_llm
from ragtime.prompters.fact_prompters import FactPrompterFR_2024_06_04

from app.infra.event_loop import ensure_event_loop


class FactGeneratorService:
    def __init__(self, model: str):
        self.prompter = FactPrompterFR_2024_06_04()
        # build_llm returns a ReasoningLLM for reasoning models (gpt-5,
        # o4-mini, opus, OVH classes) so their hidden reasoning does not
        # eat the token budget and leave the fact list empty.
        self.fact_generator = FactGenerator(llms=[build_llm(model, self.prompter)])

    def generate_facts(self, expe: Expe) -> Expe:
        try:
            logging.info(f"Generating facts for {len(expe)} questions")
            ensure_event_loop()
            self.fact_generator.generate(expe=expe)
            logging.info("Facts generated successfully")
            return expe
        except Exception as e:
            logging.error(f"Error generating facts: {str(e)}")
            raise
