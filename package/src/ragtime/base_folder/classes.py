# In this file you define the different classes used for your experiments within Ragtime :
# - an optional Retriever if you first have to get chunks
# - a Prompter for Answer generation
# - an optional Prompter for Fact generation
# - an optional Prompter for Eval generation

from typing import Optional
from ragtime.expe import QA, Chunks, Prompt, Question, WithLLMAnswer
from ragtime.generators import Prompter, Retriever


class MyRetriever(Retriever):
    def retrieve(self, qa: QA):
        # TODO : this is where you call your retriever
        # The results from the retriever are to be stored as Chunk object in a Chunks list
        # result = call_retriever(...)
        # for r in result:
        #   chunk:Chunk = make_chunk_from_r(r)
        #   qa.chunks.append(chunk)
        pass

class MyAnswerPptr(Prompter):
    def get_prompt(self, question:Question, chunks:Optional[Chunks] = None) -> Prompt:
        # This method must return a Prompt object containing a "user" and a "system" prompt
        # The prompt is then sent to the LLM
        # In the following example, the "system" prompt is empty and the "user" prompt contains only the text in the question
        # result:Prompt = Prompt()
        # result.user = f"{question.text}"
        # result.system = ""
        # return result
        pass
    
    def post_process(self, qa:QA=None, cur_obj:WithLLMAnswer=None):
        # This method is called after the generation by the LLM
        # It is called by AnswerGenerator, FactGenerator and EvalGenerator
        # The final result should be stored in "cur_obj.text"
        # The generated text is accessed in "cur_obj.llm_answer.text"
        # Other elements can be accessed in the "qa" object, for instance, qa.question, qa.chunks or qa.facts
        # In the following example, only the first letter of the generated text is kept (useful for a MCQ)
        # and the letter is compared to a "transco" table containing a value to be associated with the letter
        # This "transco" table is stored as a meta data in the question
        # The transcoded value is stored as a meta in the cur_obj
        # ans:str = cur_obj.llm_answer.text.strip()[0]
        # cur_obj.text = ans
        # transco_table:dict = qa.question.meta.get('transco', None)
        # transco:str = transco_table.get(ans, "?")
        # cur_obj.meta['transco'] = transco
        pass