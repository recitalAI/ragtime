from ragtime.prompters.prompter import Prompter
import random
from ragtime.expe import QA, Prompt, Question
import re


class QuestAnsPrompterFR(Prompter):
    """
    Generate questin from documents
    """

    def get_prompt(self, chunk) -> Prompt:
        result: Prompt = Prompt()
        result.user = f"Les informations contextuelles sont ci-dessous: \n {chunk}"
        result.system = '''Votre tâche consiste à préparer 3 questions sur le texte dans le contexte avec leur réponse complète. Les questions doivent être variées dans l'ensemble du document. Limitez les questions aux informations contextuelles fournies. Tu dois impérativement donner dans ta réponse les questions et leur réponse en suivant la même structure si dessous(sans explication supplémentaire ou autre) et chaque question et chaque réponse dans une ligne séparée(sans numérotation).
        Example :
        Qu'est ce que .... ?\nLa .....\n\n Pourquoi ...... ?\nLe .....\n\nQuand .... ?\nLa .....\n\n'''
        
        return result

    def post_process(self, qa: QA, cur_obj: Question):
        """
        Processes the answer returned by the LLM to return a list of questions
        """
        temp_list = [t.strip() for t in re.split(r'\n\n+', cur_obj.llm_answer.text) if t.strip()]
        random.shuffle(temp_list)
        divided_by_newline = [t.strip() for t in re.split(r'\n', temp_list[0]) if t.strip()]

        cur_obj.meta["question"] = divided_by_newline[0]
        cur_obj.meta["answer"] = divided_by_newline[1]
