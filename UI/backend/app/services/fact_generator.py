from ragtime.expe import Expe, Facts, Fact
from ragtime.generators import FactGenerator
from ragtime.prompters import FactPrompterJazz
from ragtime.llms import LiteLLM
import os
import logging

class FactGeneratorService:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.prompter = FactPrompterJazz()
        self.fact_generator = None

    def set_model(self, model: str):
        llm = LiteLLM(name=model, prompter=self.prompter)
        self.fact_generator = FactGenerator(llms=[llm])

    def generate_facts(self, expe: Expe) -> Expe:
        try:
            logging.info(f"Generating facts for {len(expe)} questions")
            if not self.fact_generator:
                raise ValueError("Model not set. Call set_model() before generating facts.")
            self.fact_generator.generate(expe=expe)
            logging.info("Facts generated successfully")
            return expe
        except Exception as e:
            logging.error(f"Error generating facts: {str(e)}")
            raise