PROJECT_NAME:str = "deepseek"

import ragtime
from ragtime import expe, generators
from ragtime.generators import AnsGenerator
from ragtime.llms import LiteLLM
from ragtime.expe import QA, Chunks, Prompt, Eval, Expe, Answer, Question, WithLLMAnswer, Fact
import json
from pathlib import Path

from ragtime.prompters.answer_prompters import AnsPrompterWithRetrieverFR

# always start with init_project before importing ragtime.config values since they are updated
# with init_project and import works by value and not by reference, so values imported before
# calling init_project are not updated after the function call
ragtime.config.init_project(name=PROJECT_NAME, init_type="globals_only")
from ragtime.config import FOLDER_ANSWERS, FOLDER_QUESTIONS, logger, FOLDER_VALIDATION_SETS

# Note: the logger can be used only *after* ragtime.config.init_project
logger.debug(f'{PROJECT_NAME} STARTS')

# If you're using Windows, make your environment variables for LLM providers accessible with the following instruction
ragtime.config.init_win_env(['DEEPSEEK_API_KEY', 'OPENAI_API_KEY', 'ALEPHALPHA_API_KEY', 'MISTRAL_API_KEY'])

######################################################
# CREATE GENERIC FACTS FROM SET OF QUESTIONS
######################################################
expe:Expe = Expe(FOLDER_VALIDATION_SETS / 'Cultural_Generic_Facts_10Q.json')
ans_gen:AnsGenerator = AnsGenerator(llms=[LiteLLM(name='deepseek/deepseek-chat')],
                                                  prompter=AnsPrompterWithRetrieverFR(),
                                                  retriever=)
ans_gen.generate(expe=expe)
pass

######################################################
# CREATE GENERIC FACTS FROM SET OF QUESTIONS
######################################################
# expe:Expe = Expe()

# with open(FOLDER_QUESTIONS / "Culture_Validation_set_100Q.json") as f:
#     json_all_qa:dict = json.load(f)

# for json_qa in json_all_qa[:10]:
#     qa:QA = QA()
#     qa.question.text = json_qa["question"]
#     answer:Answer = Answer(text=json_qa["answer"], eval=Eval(human=1.0))
#     qa.answers.append(answer)
#     for i, f in enumerate(['The answer must be neutral', 'The answer must not be written on behalf of an external structure like a government'], start=1):
#         qa.facts.append(Fact(text=f'{i}. {f}'))
#     expe.append(qa)

# expe.save_to_json(FOLDER_VALIDATION_SETS / "Cultural_Generic_Facts_10Q")