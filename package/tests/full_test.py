PROJECT_NAME:str = "test"

from pathlib import Path
import shutil
from typing import Optional
import ragtime
from ragtime import expe, generators
from ragtime.expe import QA, Chunks, Prompt, Question, WithLLMAnswer

# always start with init_project before importing ragtime.config values since they are updated
# with init_project and import works by value and not by reference, so values imported before
# calling init_project are not updated after the function call
ragtime.config.init_project(name=PROJECT_NAME, init_type="delete_if_exists")
from ragtime.config import FOLDER_ANSWERS, FOLDER_QUESTIONS, logger

logger.debug(f'"{PROJECT_NAME}" starts')

class MCQAnsPptr(generators.Prompter):
    def get_prompt(self, question:Question, chunks:Optional[Chunks] = None) -> Prompt:
        result:Prompt = Prompt()
        result.user = f"{question.text}"
        result.system = "Répond uniquement avec la lettre. Ne donne qu'une seule réponse."
        return result
    
    def post_process(self, qa:QA=None, cur_obj:WithLLMAnswer=None):
        ans:str = cur_obj.llm_answer.text.strip()[0] # gets the raw output from the LLM, remove blanks and keep 1 character
        cur_obj.text = ans # assign this letter as the text of the current Answer being built
        transco_table:dict = qa.question.meta.get('transco', None) # try to retrieve the Transco dict associated with the current question
        transco:str = transco_table.get(ans, "?") if transco_table else "?" # get the value associated with the letter in the Answer - "?"" if not found
        cur_obj.meta['transco'] = transco # stored the value in the Answer's meta data, key "transco"

test_file:str = 'test_quest.json'
shutil.copy(test_file, FOLDER_QUESTIONS)
generators.gen_Answers(folder_in=FOLDER_QUESTIONS, folder_out=FOLDER_ANSWERS,
                        json_file=test_file,
                        prompter=MCQAnsPptr(),
                        llm_names=["gpt-3.5-turbo", "mistral/mistral-large-latest"])

logger.debug(f'"{PROJECT_NAME}" ends')