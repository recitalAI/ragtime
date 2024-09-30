from ragtime.prompters import Prompter
from ragtime.expe import QA, Prompt, Facts, Fact, Answer, Question


class FactPrompterJazz(Prompter):
    """
    New version of Facts Prompters - generate less Facts than the version of 2024_06-04
    In this new version, the System prompt ask to generate few Facts and adds the original Question
    The User Prompt thus provides both the Paragraph and the Question
    """

    system:str = """Génère des phrases numérotées courtes et simples qui décrivent ce PARAGRAPHE.
Génère le moins de phrases possibles.
Ne génère que des phrases qui permettent de répondre à la QUESTION.
Chaque phrase ne doit contenir qu'une seule information.
Les phrases ne doivent pas contenir de référence à un document, un paragraphe, une source ou une page.
Ne génère aucune phrase redondante."""

    def get_prompt(self, question: Question, answer: Answer) -> Prompt:
        result: Prompt = Prompt()
        result.user = f"PARAGRAPHE: {answer.text}\nQUESTION: {question.text}"
        result.system = self.system
        return result

    def post_process(self, qa: QA, cur_obj: Facts):
        """
        Processes the answer returned by the LLM to return a list of Fact
        Can be overriden to fit specific prompts
        """
        temp_list: list[str] = [
            t.strip() for t in cur_obj.llm_answer.text.split("\n") if t.strip()
        ]
        temp_list = [
            Fact(text=f"{i}. {t}" if t[1] != "." and t[2] != "." else t)
            for i, t in enumerate(temp_list, start=1)
            if len(t) > 2
        ]
        cur_obj.items = temp_list

class FactPrompterFR_2024_06_04(Prompter):
    """
    Previous version of Facts Prompters - used on Jun 4th 2024
    This version used to generate too many Facts
    """

    system:str = """Génère un minimum de phrases numérotées courtes et simples qui décrivent ce paragraphe.
Chaque phrase ne doit contenir qu'une seule information.
Chaque phrase doit être indépendante et aucune phrase ne doit contenir la même information qu'une autre phrase.
Les phrases ne doivent pas contenir de référence au document source ni à sa page.
Les phrases doivent être compréhensibles seules et donc ne pas contenir de référence aux autres phrases ni nécessiter les autres phrases pour être comprises."""

    def get_prompt(self, question: Question, answer: Answer) -> Prompt:
        result: Prompt = Prompt()
        result.user = f"{answer.text}"
        result.system = self.system
        return result

    def post_process(self, qa: QA, cur_obj: Facts):
        """
        Processes the answer returned by the LLM to return a list of Fact
        Can be overriden to fit specific prompts
        """
        temp_list: list[str] = [
            t.strip() for t in cur_obj.llm_answer.text.split("\n") if t.strip()
        ]
        temp_list = [
            Fact(text=f"{i}. {t}" if t[1] != "." and t[2] != "." else t)
            for i, t in enumerate(temp_list, start=1)
            if len(t) > 2
        ]
        cur_obj.items = temp_list
