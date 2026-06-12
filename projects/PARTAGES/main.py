PROJECT_NAME:str = "PARTAGES"

import ragtime
from ragtime import expe, generators
from ragtime.expe import QA, Answers, Chunks, Expe, Prompt, Question, WithLLMAnswer
from ragtime.generators.answer_generator import AnsGenerator
from ragtime.generators.eval_generator import EvalGenerator
from ragtime.llms.llm import LiteLLM
from ragtime.prompters.answer_prompters import AnsPrompterBase
from ragtime.prompters.eval_prompters import EvalPrompterFR, EvalPrompterFRV2
from ragtime.prompters.fact_prompters import FactPrompterFR_2024_06_04, FactPrompterJazz
from ragtime.generators import FactGenerator
from classes import PARTAGESAnswerPrompter, PARTAGESEvalPrompter

# always start with init_project before importing ragtime.config values since they are updated
# with init_project and import works by value and not by reference, so values imported before
# calling init_project are not updated after the function call
ragtime.config.init_project(name=PROJECT_NAME, init_type="globals_only")
from ragtime.config import FOLDER_ANSWERS, FOLDER_EVALS, FOLDER_QUESTIONS, logger, FOLDER_VALIDATION_SETS

# Note: the logger can be used only *after* ragtime.config.init_project
logger.debug(f'*** PROJECT "{PROJECT_NAME}" STARTS')

# If you're using Windows, make your environment variables for LLM providers accessible with the following instruction
ragtime.config.init_win_env(['OPENAI_API_KEY', 'MISTRAL_API_KEY'])


# # # FACTS
# expe:Expe = Expe(FOLDER_ANSWERS / "qa_20260518_122441.json")
# fact_gen:FactGenerator = FactGenerator(llms=[LiteLLM(name='mistral/mistral-small-latest', prompter=FactPrompterFR_2024_06_04())])
# fact_gen.generate(expe=expe)
# expe.save_to_json(path=FOLDER_VALIDATION_SETS)

## CLEAR ANSWERS
# expe:Expe = Expe(FOLDER_VALIDATION_SETS / "qa_20260518_122441--5Q_0C_38F_0M_5A_5HE_0AE_2026-05-18_12h27,58.json")
# for qa in expe: qa.answers = Answers()
# expe.save_to_json(b_overwrite=True)


# # ANSWERS
# ans_gen:AnsGenerator = AnsGenerator(llms=[LiteLLM(name='mistral/mistral-small-latest', prompter=PARTAGESAnswerPrompter())])
# ans_gen.generate(expe=expe)
# expe.save_to_json(FOLDER_ANSWERS)

# # EVALUATION
expe:Expe = Expe(FOLDER_ANSWERS / "qa_20260518_122441--5Q_0C_38F_1M_5A_0HE_0AE_2026-05-18_22h10,42.json")
eval_gen:EvalGenerator = EvalGenerator(llms=[LiteLLM(name='mistral/mistral-small-latest', prompter=PARTAGESEvalPrompter())])
eval_gen.generate(expe=expe)
expe.save_to_json(path=FOLDER_EVALS)

# GEN REPORT
# expe:Expe = Expe(FOLDER_EVALS / "qa_20260518_122441--5Q_0C_38F_0M_0A_0HE_0AE_2026-05-18_22h30,55.json")
# expe.save_to_spreadsheet()