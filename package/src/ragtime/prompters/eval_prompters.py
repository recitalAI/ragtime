from ragtime.prompters.prompter import Prompter

from ragtime.expe import QA, Prompt, Facts, Answer, Eval, Question, Fact, Chunks
from ragtime.base import div0
import markdown

import re


class EvalPrompterFR(Prompter):
    """
    Prompt: FAITS and REPONSE - expect the REPONSE to be rewritten including the FACTS in the text
    Post_process: analyse cited factsfacts not cited, and facts invented (?)
    """

    system: str = """Tu dois comparer une liste numérotée de FAITS avec une REPONSE.
        Tu dois reprendre exactement la REPONSE en insérant dans le texte le numéro du FAIT auquel correspond exactement le passage ou la phrase.
        Si la phrase correspond à plusieurs FAITS, indique les entre parenthèses.
        Il ne faut pas insérer le FAIT s'il est en contradiction avec le passage ou la phrase.
        Si un passage ou une phrase dans la REPONSE ne correspond à aucun FAIT il faut mettre un point d'interrogation entre parenthèses (?)
        sauf si ce passage fait référence à un emplacement dans le document, auquel cas il ne faut rien indiquer."""

    def get_prompt(self, answer: Answer, facts: Facts) -> Prompt:
        result: Prompt = Prompt()
        facts_as_str: str = "\n".join(f"{i}. {fact.text}" for i, fact in enumerate(facts, start=1))
        result.user = f"-- FAITS --\n{facts_as_str}\n\n-- REPONSE --\n{answer.text}"
        result.system = self.system
        return result

    def post_process(self, qa: QA, cur_obj: Eval):
        answer: str = cur_obj.llm_answer.text if cur_obj.llm_answer.text != "[]" else ""
        answer = answer.replace("(FAIT ", "(")  # removes the word FAIT before the fact number as it is sometimes generated in the answer
        # get the set of facts numbers from answer
        facts_in_answer: set[int] = set([int(s) for s in ",".join(re.findall("\([\d+,+\s+]+\)", answer)).replace("(", "").replace(")", "").split(",") if s])
        # get the numbers in the true facts
        true_facts: set[int] = set([int(s.text[0] if s.text[1] == "." else s.text[:2]) for s in qa.facts if s])
        true_facts_in_answer: set[int] = facts_in_answer & true_facts
        true_facts_not_in_answer: set[int] = true_facts - true_facts_in_answer
        # get the number of extra facts (?) - they are not always hallucinations, sometimes just true facts not interesting and not included as usefule facts
        nb_extra_facts_in_answer: int = len(re.findall("\(\?\)", answer))
        # compute metrics
        precision: float = div0(len(true_facts_in_answer), len(facts_in_answer) + nb_extra_facts_in_answer)
        recall: float = div0(len(true_facts_in_answer), len(true_facts))
        cur_obj.meta["precision"] = precision
        cur_obj.meta["recall"] = recall
        cur_obj.meta["extra"] = nb_extra_facts_in_answer
        cur_obj.meta["missing"] = ", ".join(str(v) for v in list(true_facts_not_in_answer))
        cur_obj.meta["nb_missing"] = len(true_facts_not_in_answer)
        cur_obj.meta["facts_in_ans"] = str(sorted(facts_in_answer))
        cur_obj.auto = div0(2 * precision * recall, precision + recall)
        cur_obj.text = markdown.markdown(answer)


class EvalPrompterFRV2(Prompter):
    """
    Prompt: FAITS and REPONSE - expect the REPONSE to be rewritten including the FACTS in the text
    Post_process: analyse cited factsfacts not cited, and facts invented (?)
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
            [int(match) for match in re.findall(r'(\d+)\.\s*\[?OK\]?', answer)])
        hallus_in_answer: set[int] = set(
            [int(match) for match in re.findall(r'(\d+)\.\s*\[?HALLU\]?', answer)])
        # get the numbers in the true facts
        true_facts: set[int] = set(
            [int(s.text[0] if s.text[1] == "." else s.text[:2]) for s in qa.facts if s])
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

class EvalPrompterChunks(Prompter):

    system: str = """Évaluez la réponse du LLM par rapport à la QUESTION et aux CHUNKS fournis.

1. Pour chaque FAIT dans les CHUNKS du LLM, déterminez s'il est :
   [OK] - Correct et soutenu par les CHUNKS
   [HALLU] - Incorrect ou contredit par les CHUNKS
   [MISSING] - Absent des CHUNKS
2. Dans le cas [OK] ou [HALLU], une explication des points de contradiction ou d'accord entre le CHUNK et le FAIT.
3. citez la partie pertinente des CHUNKS dans le PARAGRAPHE liée au fait.

Format de réponse :

[Fait 1]

Statut : [OK/HALLU/MISSING]
Explication : [Votre analyse]
Les chunks (si applicable) : "[numéro des CHUNKS]"
Source (si applicable) : "[Citation des CHUNKS]"

[Fait 2]
...

N.B. : 
- Donne le numéro du fait tel qu'il est présenté dans le message, sans tenir compte de l'ordre.
- N'évaluez les faits dans les CHUNKS que lorsque la réponse du LLM présente une erreur ([HALLU] ou [MISSING]).
- Répondez de manière concise et directe, en suivant strictement le format demandé.
- Assurez-vous d'évaluer tous les FAITS présents dans les CHUNKS du LLM.
        """

    def get_prompt(self, question: Question, facts: list[Fact], chunks: Chunks) -> Prompt:
        result: Prompt = Prompt()
        facts_as_str: str = "\n".join(
            f"{fact.text}" for i, fact in enumerate(facts, start=1))
        chunks_as_str: str = "\n".join(
            f"\n\n Chunk_{i}. {chunk.text}" for i, chunk in enumerate(chunks, start=1))
        result.user = f"-- QUESTION --\n{question.text}\n\n-- FAITS --\n{facts_as_str}\n\n-- CHUNK --\n{chunks_as_str}"
        result.system = self.system
        return result


    def post_process(self, qa: QA, cur_obj: Eval):
        answer: str = cur_obj.llm_answer.text if cur_obj.llm_answer.text != "[]" else ""
        facts = re.findall(r"\[Fait (\d+)\]", answer)
        missing_facts = re.findall(r"\[Fait (\d+)\]\s*Statut\s*:\s*\[?MISSING\]?", answer)
        ok_facts = re.findall(r"\[Fait (\d+)\]\s*Statut\s*:\s*\[?OK\]?", answer)
        hallucination_facts = re.findall(r"\[Fait (\d+)\]\s*Statut\s*:\s*\[?HALLU\]?", answer)
                # compute metrics
        cur_obj.meta["missing"] = list(missing_facts)
        cur_obj.meta["nb_missing"] = len(missing_facts)
        cur_obj.meta["ok"] = list(ok_facts)
        cur_obj.meta["nb_ok"] = len(ok_facts)
        cur_obj.meta["hallu"] = list(hallucination_facts)
        cur_obj.meta["nb_hallu"] = len(hallucination_facts)

        cur_obj.text = markdown.markdown(answer)