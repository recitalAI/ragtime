from typing import Optional
from ragtime.expe import QA, Prompt, Question, Chunks, Answer
from ragtime.prompters import Prompter
from ragtime.config import logger
import markdown
from langdetect import detect
import json
from unidecode import unidecode
from typing import Optional

class AnsPrompterBase(Prompter):
    """
    This simple prompter just send the question as is to the LLM
    and does not perform any post-processing
    """
    system:str = ""

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

class AnsPrompterWithRetrieverFR(Prompter):
    """
    This new prompter is supposed to generate shorter answers than the one from 2024-06-04
    This prompter uses a prompt asking the LLM to generate a JSON structure
    and includes chunks in its prompt. It performs post-processing to exploit
    the JSON structure the LLM is supposed to generate.
    """

    FLD_QUEST_OK: str = "q_ok"
    FLD_CHUNKS_OK: str = "chunks_ok"
    FLD_ANSWER: str = "answer"

    system:str = f"""
Tu es un expert qui doit répondre à des questions à l'aide de paragraphes qui te sont fournis.
Ta réponse doit être au format JSON suivant :
- "{FLD_QUEST_OK}": 1 si la question a un sens, 0 sinon
- "{FLD_CHUNKS_OK}": 1 si les paragraphes fournis sont suffisants pour répondre, 0 sinon
- "{FLD_ANSWER}": la réponse, avec les titres et les pages des documents

Les paragraphes sont présentés ainsi :
- Titre (Page X)
Contenu
    """

    def get_prompt(self, question: Question, chunks: Optional[Chunks] = None) -> Prompt:
        """
        This Answer prompt asks for a JSON answer
        """

        # Format string to convert a chunk into a string
        fmt_chunk_to_str: str = """- {title} (p. {page})
        {text}"""

        # Format string to join the strings representing the different chunks
        str_joint: str = "\n\n"

        # Format string to convert the string containing all the chunks to a user prompt
        # fmt_chunks_to_user_msg: str = """{chunks}
        # La question est '{question}'"""
        fmt_chunks_to_user_msg: str = """{chunks}
        
        Question: {question}"""

        # System prompt
        system_msg: str = self.system

        result: Prompt = Prompt()
        # Compute the user prompt
        chunks_as_list: list[str] = [
            fmt_chunk_to_str.format(
                title=chunk.meta["display_name"],
                page=chunk.meta["page_number"],
                text=chunk.text,
            )
            for chunk in chunks
        ]
        chunks_as_str: str = str_joint.join(chunks_as_list)
        result.user = fmt_chunks_to_user_msg.format(
            chunks=chunks_as_str, question=question.text
        )

        # Get the system prompt
        result.system = system_msg

        return result

    def post_process(self, qa: QA, cur_obj: Answer):
        """
        Do JSON post processing (i.e. tries to extract correct JSON in an incorrect
        format) and finds the sources chunks quoted in the generated answer
        """

        def fmt_name(a_str: str) -> str:
            """
            Internal function used to format the documents' references
            """
            result: str = unidecode(a_str)
            rep_str: list[tuple(str, str)] = [  # type: ignore
                ("a la page", "p"),
                ("aux pages", "p"),
                ("page", "p"),
                (" ", ""),
                (".pdf", ""),
                (".pptx", ""),
                (".", ""),
                ("'", ""),
                ('"', ""),
                ("(", ""),
                (")", ""),
                (",", ""),
                ("-", ""),
            ]
            for c in rep_str:
                result = result.replace(*c)
            return result

        # deprecated answer.text_field = "answer" # tells the Answer to fetch the value from the meta "answer", not the original "text" field
        # which contains the raw text returned by the LLM in this case
        json_ok: bool = False
        # test JSON and tries to extract fields if needed
        json_ans: dict = {}
        if not cur_obj.llm_answer:
            logger.error(
                f"Nothing to post-process! LLMAnswer is None for current Answer!"
            )
            return
        cur_obj.text = cur_obj.llm_answer.text
        try:
            json_ans: dict = json.loads(cur_obj.text)
            json_ok = True
        except:
            ans_text: str = cur_obj.text[
                cur_obj.text.find("{") : cur_obj.text.find("}") + 1
            ]
            ans_text = ans_text.replace("\n", "").replace("\\", "").replace("   ", " ")
            ans_text = ans_text.replace("'}", '"}')
            t: str = ans_text
            p1: int = t.find(f'"{self.FLD_ANSWER}"') + len(f'"{self.FLD_ANSWER}": "')
            p2: int = t.rfind('"')
            ans_text = t[:p1] + t[p1:p2].replace('"', "'") + t[p2:]
            try:
                json_ans = json.loads(ans_text)
                json_ok = True
            except:
                pass

        # Fills the fields with values from the returned JSON if ok
        cur_obj.meta["json_ok"] = json_ok
        cur_obj.meta["question_ok"] = (
            bool(json_ans[self.FLD_QUEST_OK]) if json_ok else None
        )
        cur_obj.meta["chunks_ok"] = (
            bool(json_ans[self.FLD_CHUNKS_OK]) if json_ok else None
        )
        cur_obj.text = json_ans[self.FLD_ANSWER] if json_ok else cur_obj.llm_answer.text

        # Get Answers's lang
        try:
            lang: str = detect(cur_obj.llm_answer.text)
            cur_obj.meta["lang"] = lang
        except:
            cur_obj.meta["lang"] = None

        # Calc nb sources in answer even if the JSON is not formatted well
        ans_formatted: str = fmt_name(cur_obj.llm_answer.text)
        docs_in_chunks: dict[str, str] = {
            c.meta["display_name"]: fmt_name(c.meta["display_name"]) for c in qa.chunks
        }
        docs_page_in_chunks: dict[str] = {
            f'{c.meta["display_name"]} p.{c.meta["page_number"]}': fmt_name(
                f'{c.meta["display_name"]}p.{c.meta["page_number"]}'
            )
            for c in qa.chunks
        }
        cur_obj.meta["docs_in_ans"] = [
            orig_name
            for (orig_name, fmt_name) in docs_in_chunks.items()
            if fmt_name in ans_formatted
        ]
        cur_obj.meta["docs_and_page_in_ans"] = [
            orig_name
            for (orig_name, fmt_name) in docs_page_in_chunks.items()
            if fmt_name in ans_formatted
        ]

class AnsPrompterWithRetrieverFR_2024_06_04(Prompter):
    """
    Old version of the Answer Prompter with Retriever - used to generate a bit longer answers
    """

    FLD_QUEST_OK: str = "q_ok"
    FLD_CHUNKS_OK: str = "chunks_ok"
    FLD_ANSWER: str = "answer"

    system:str = f"""Tu es un expert qui doit répondre à des questions à l'aide de paragraphes qui te sont fournis.
        Tu dois utiliser uniquement ces paragraphes pour répondre aux questions.
        Tu dois inclure les titres exacts de ces paragraphes dans la réponse que tu renvoies.
        Tu dois justifier tes réponses et expliquer comment tu les as construites.
        Tu dois détailler les phrases et les mots qui te permettent de générer ta réponse.

        Les paragraphes sont présentés ainsi :
        - Titre (Page X)
        Contenu

        La réponse générée doit indiquer clairement la source avec le Titre et la Page.

        La réponse doit utiliser le format JSON suivant :
        {{
        "{FLD_QUEST_OK}": 0 ou 1,
        "{FLD_CHUNKS_OK}": 0 ou 1,
        "{FLD_ANSWER}": une chaîne de caractères contenant la réponse
        }}

        Le champ "{FLD_QUEST_OK}" vaut 0 si la question n'est pas claire, 1 sinon.
        Le champ "{FLD_CHUNKS_OK}" vaut 0 si les paragraphes fournis ne permettent pas de répondre à la question, 1 sinon.
        Le champ "{FLD_ANSWER}" contient la réponse."""

    def get_prompt(self, question: Question, chunks: Optional[Chunks] = None) -> Prompt:
        """
        This Answer prompt asks for a JSON answer
        """

        # Format string to convert a chunk into a string
        fmt_chunk_to_str: str = """- {title} (p. {page})
        {text}"""

        # Format string to join the strings representing the different chunks
        str_joint: str = "\n\n"

        # Format string to convert the string containing all the chunks to a user prompt
        # fmt_chunks_to_user_msg: str = """{chunks}
        # La question est '{question}'"""
        fmt_chunks_to_user_msg: str = """{chunks}
        
        Question: {question}"""

        # System prompt
        system_msg: str = self.system

        result: Prompt = Prompt()
        # Compute the user prompt
        chunks_as_list: list[str] = [
            fmt_chunk_to_str.format(
                title=chunk.meta["display_name"],
                page=chunk.meta["page_number"],
                text=chunk.text,
            )
            for chunk in chunks
        ]
        chunks_as_str: str = str_joint.join(chunks_as_list)
        result.user = fmt_chunks_to_user_msg.format(
            chunks=chunks_as_str, question=question.text
        )

        # Get the system prompt
        result.system = system_msg

        return result

    def post_process(self, qa: QA, cur_obj: Answer):
        """
        Do JSON post processing (i.e. tries to extract correct JSON in an incorrect
        format) and finds the sources chunks quoted in the generated answer
        """

        def fmt_name(a_str: str) -> str:
            """
            Internal function used to format the documents' references
            """
            result: str = unidecode(a_str)
            rep_str: list[tuple(str, str)] = [  # type: ignore
                ("a la page", "p"),
                ("aux pages", "p"),
                ("page", "p"),
                (" ", ""),
                (".pdf", ""),
                (".pptx", ""),
                (".", ""),
                ("'", ""),
                ('"', ""),
                ("(", ""),
                (")", ""),
                (",", ""),
                ("-", ""),
            ]
            for c in rep_str:
                result = result.replace(*c)
            return result

        # deprecated answer.text_field = "answer" # tells the Answer to fetch the value from the meta "answer", not the original "text" field
        # which contains the raw text returned by the LLM in this case
        json_ok: bool = False
        # test JSON and tries to extract fields if needed
        json_ans: dict = {}
        if not cur_obj.llm_answer:
            logger.error(
                f"Nothing to post-process! LLMAnswer is None for current Answer!"
            )
            return
        cur_obj.text = cur_obj.llm_answer.text
        try:
            json_ans: dict = json.loads(cur_obj.text)
            json_ok = True
        except:
            ans_text: str = cur_obj.text[
                cur_obj.text.find("{") : cur_obj.text.find("}") + 1
            ]
            ans_text = ans_text.replace("\n", "").replace("\\", "").replace("   ", " ")
            ans_text = ans_text.replace("'}", '"}')
            t: str = ans_text
            p1: int = t.find(f'"{self.FLD_ANSWER}"') + len(f'"{self.FLD_ANSWER}": "')
            p2: int = t.rfind('"')
            ans_text = t[:p1] + t[p1:p2].replace('"', "'") + t[p2:]
            try:
                json_ans = json.loads(ans_text)
                json_ok = True
            except:
                pass

        # Fills the fields with values from the returned JSON if ok
        cur_obj.meta["json_ok"] = json_ok
        cur_obj.meta["question_ok"] = bool(json_ans[self.FLD_QUEST_OK]) if json_ok else None
        cur_obj.meta["chunks_ok"] = bool(json_ans[self.FLD_CHUNKS_OK]) if json_ok else None
        cur_obj.text = json_ans[self.FLD_ANSWER] if json_ok else cur_obj.llm_answer.text

        # Get Answers's lang
        try:
            lang: str = detect(cur_obj.llm_answer.text)
            cur_obj.meta["lang"] = lang
        except:
            cur_obj.meta["lang"] = None

        # Calc nb sources in answer even if the JSON is not formatted well
        ans_formatted: str = fmt_name(cur_obj.llm_answer.text)
        docs_in_chunks: dict[str, str] = {
            c.meta["display_name"]: fmt_name(c.meta["display_name"]) for c in qa.chunks
        }
        docs_page_in_chunks: dict[str] = {
            f'{c.meta["display_name"]} p.{c.meta["page_number"]}': fmt_name(
                f'{c.meta["display_name"]}p.{c.meta["page_number"]}'
            )
            for c in qa.chunks
        }
        cur_obj.meta["docs_in_ans"] = [
            orig_name
            for (orig_name, fmt_name) in docs_in_chunks.items()
            if fmt_name in ans_formatted
        ]
        cur_obj.meta["docs_and_page_in_ans"] = [
            orig_name
            for (orig_name, fmt_name) in docs_page_in_chunks.items()
            if fmt_name in ans_formatted
        ]