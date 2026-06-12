# In this file you define the different classes used for your experiments within Ragtime :
# - an optional Retriever if you first have to get chunks
# - a Prompter for Answer generation
# - an optional Prompter for Fact generation
# - an optional Prompter for Eval generation

import re
from typing import Optional
import markdown
from ragtime.base import div0
from ragtime.expe import QA, Answer, Chunks, Eval, Facts, Prompt, Question, WithLLMAnswer
from ragtime.generators import Prompter, Retriever

class PARTAGESAnswerPrompter(Prompter):
    """
    This simple prompter just send the question as is to the LLM
    and does not perform any post-processing
    """
    system:str = "Tu es un médecin qui doit rédiger une conclusion par rapport à un compte-rendu médical." \
    "La conclusion doit être courte et factuelle et inclure une codification si possible."

    def get_prompt(self, question: Question, chunks: Optional[Chunks] = None) -> Prompt:
        result: Prompt = Prompt()
        result.user = f"{question.text}"
        result.system = self.system
        return result

    def post_process(self, qa: QA = None, cur_obj: Answer = None):
        """
        Does not do anything by default, but can be overridden to add fields in meta data for instance
        """
        cur_obj.text = markdown.markdown(cur_obj.llm_answer.text)

class PARTAGESEvalPrompter(Prompter):
    """
    Prompt: FAITS and REPONSE - expect the REPONSE to be rewritten including the FACTS in the text
    Post_process: analyse cited facts not cited, and facts invented (?)
    """

    system: str = """
    Pour chaque fait dans une liste de FAITS, déterminez si le fait est soutenu dans le PARAGRAPHE ou non et retournez :
    - [OK] si le fait est soutenu, [NOT FOUND] s'il n'est pas soutenu et [HALLU] si un fait opposé est soutenu
    - la raison pour laquelle vous retournez OK, NON TROUVÉ ou HALLU
    - la partie dans le PARAGRAPHE liée à la raison
    À la fin de la réponse, ajoutez "[EXTRA] = nombre d'idées trouvées dans le PARAGRAPHE qui ne correspondent pas aux idées factuelles." Une idée est considérée comme [EXTRA] si :
    - Hors sujet
    - Elle donne des informations différentes des idées factuelles.
    - Contexte supplémentaire non désiré.

    ## Format de réponse :

    1. [Statut] - [Explication de comment le paragraphe soutient ou ne soutient pas le Fait 1]
    Partie dans le paragraphe : "[Citation pertinente du paragraphe]"

    2. [Statut] - [Explication de comment le paragraphe soutient ou ne soutient pas le Fait 2]
    Partie dans le paragraphe : "[Citation pertinente du paragraphe]"

    ...

    [EXTRA] = [Nombre de faits ou d'informations supplémentaires dans le paragraphe non mentionnés dans les faits]
        """

    def get_prompt(self, answer: Answer, facts: Facts) -> Prompt:
        result: Prompt = Prompt()
        facts_as_str: str = "\n".join(
            f"{i}. {fact.text}" for i, fact in enumerate(facts, start=1))
        result.user = f"-- FAITS --\n{facts_as_str}\n\n-- PARAGRAPH --\n{answer.text}"
        result.system = self.system
        return result

    def post_process(self, qa: QA, cur_obj: Eval):
        answer: str = cur_obj.llm_answer.text if cur_obj.llm_answer.text != "[]" else ""
        # removes the word FAIT before the fact number as it is sometimes generated in the answer
        answer = answer.replace("(FAIT ", "(")
        # get the set of facts numbers from answer
        facts_in_answer: set[int] = set(
            [int(match) for match in re.findall(r'(\d+)\.[\s\*]*\[OK\]?', answer)])
        hallus_in_answer: set[int] = set(
            [int(match) for match in re.findall(r'(\d+)\.[\s\*]*\[HALLU\]?', answer)])
        # get the numbers in the true facts - add them if not present
        true_facts: set[int] = set()
        for i, f in enumerate(qa.facts, start=1):
            m = re.search(r"\d+\.", f.text)
            true_facts.add(int(m.group()[:-1]) if m else i)
        # true_facts: set[int] = set(
        #     [int(s.text[0] if s.text[1] == "." else s.text[:2]) for s in qa.facts if s])
        true_facts_in_answer: set[int] = facts_in_answer & true_facts
        hallus_in_answer: set[int] = hallus_in_answer & true_facts
        true_facts_not_in_answer: set[int] = true_facts - \
            (true_facts_in_answer | hallus_in_answer)
        # get the number of extra facts (?) - they are not always hallucinations, sometimes just true facts not interesting and not included as usefule facts
        Extra = re.findall(r'\[EXTRA\]\s*=\s*(\d+)', answer)
        Extra_text = re.findall(r'\[EXTRA\]\s*=\s*\d+\s*(.*)', answer)
        nb_extra_facts_in_answer: int = int(Extra[0]) if Extra != [] else 0

        # compute metrics
        cur_obj.meta["extra"] = " ".join(Extra_text)
        cur_obj.meta["nb_extra"] = nb_extra_facts_in_answer
        cur_obj.meta["missing"] = [i for i in true_facts_not_in_answer]
        cur_obj.meta["nb_missing"] = len(true_facts_not_in_answer)
        cur_obj.meta["ok"] = list(true_facts_in_answer)
        cur_obj.meta["nb_ok"] = len(true_facts_in_answer)
        cur_obj.meta["hallu"] = list(hallus_in_answer)
        cur_obj.meta["nb_hallu"] = len(hallus_in_answer)
        cur_obj.auto = max(0, div0(len(true_facts_in_answer) - len(hallus_in_answer), len(true_facts)) -
                           0.25*div0(len(true_facts_not_in_answer) + nb_extra_facts_in_answer, len(true_facts)))
        cur_obj.text = markdown.markdown(answer)