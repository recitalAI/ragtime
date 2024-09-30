from ragtime.base import call_api, REQ_GET, REQ_POST, div0
from ragtime.prompters import Prompter
from ragtime.llms import LLM
from ragtime.expe import QA, Prompt, Answer,Fact, Facts, Eval, LLMAnswer, Question,Chunks, Chunk
from ragtime.config import logger
import re
import json
import os
from datetime import datetime, timedelta
import asyncio
import markdown
import requests
from typing import Dict, Any, ClassVar
from ragtime.retrievers import Retriever

LSA_USERNAME: str = "imad+ragtime@recital.ai"
LSA_PASSWORD: str = "Mido@123"
LSA_URL_LOGIN: str = "https://search.dev.auth.recital.ai/auth/api/v1/login/"
LSA_URL_SEARCH: str = "https://search.dev.api.recital.ai/search/api/v1/search/legacy"

class Search(Retriever):
    """
    LSA Retriever queries reciTAL Search
    """
    token: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3MjYxNDg2OTQuMDMwODEzLCJwcm9kdWN0cyI6WyJzZWFyY2giXSwidHlwZSI6ImFwaV90b2tlbiIsInByb2R1Y3QiOm51bGwsInVzZXJfaWQiOjU0LCJvcmdfaWQiOjE2LCJyb2xlIjoib3JnYWRtaW4iLCJpc19kYXRhc2NpZW50aXN0IjpmYWxzZSwiZ3JvdXBfaWRzIjpbXSwic2VydmljZSI6bnVsbH0.XMWquXqGXxhsGU2X50YZSgJ8uQrv8AhxtXG__1ImC5s"
    token_last_update: datetime = None
    TOKEN_DURATION: int = 1  # max token duration in hours

    def retrieve(self, qa: QA):
        """
        - the meta "team" contains the team filter to be sent to the retriever - it is a meta attached to the Question
        - it returns a chunk with the following meta fields:
            - text: chunk's text
            - score: confidence score
            - url: doc url on the right page
            - display_name: friendly version of the file name
            - page_number: page number of the chunk within the source document
            - image: url to the image representing the chunk
        """
        logger.debug(f'Start LSA Retriever')
        self._refresh_token()
        qa.chunks.empty()

        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token}"
        }

        params: Dict[str, Any] = {
            "query": qa.question.text
        }

        if "folder_id" in qa.question.meta:
            params["folder_id"] = qa.question.åmeta["folder_id"]

        try:
            response = requests.post(LSA_URL_SEARCH, headers=headers, params=params, json={})
            response.raise_for_status()
            search_results = response.json()
                        
            chunks = search_results.get("chunks", [])
            
            for i, search_chunk in enumerate(chunks):
                
                chunk = Chunk()
                
                # Try to extract text content
                if 'content' in search_chunk:
                    if isinstance(search_chunk['content'], dict):
                        chunk.text = search_chunk['content'].get('content', '')
                        chunk.meta["content_type"] = search_chunk['content'].get('content_type', 'unknown')
                    elif isinstance(search_chunk['content'], str):
                        chunk.text = search_chunk['content']
                        chunk.meta["content_type"] = 'text'
                    else:
                        logger.warning(f"Unexpected content format in chunk {i+1}")
                        continue
                else:
                    logger.warning(f"No 'content' field found in chunk {i+1}")
                    continue
                
                # Extract score
                chunk.meta["score"] = search_chunk.get('score', 0)
                chunk.meta["display_name"] = search_chunk.get('meta', {}).get('path','')
                chunk.meta["page_number"] = search_chunk.get('meta', {}).get('page','')
                
                # Extract other metadata
                for key, value in search_chunk.get("meta", {}).items():
                    if key != "explanation":
                        chunk.meta[key] = value
                
                qa.chunks.append(chunk)
                logger.debug(f"Successfully processed chunk {i+1}")
            
            logger.debug(f'Retrieved {len(qa.chunks)} chunk(s)')
        
        except requests.RequestException as e:
            logger.error(f"Error making request to LSA search API: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON response: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in retrieve method: {str(e)}")

    def _refresh_token(self):
        if (self.token != ""):
            self._token = self.token
        elif (self.token == "") or (datetime.now() - self.token_last_update).total_seconds() > self.TOKEN_DURATION * 3600:
            headers = {"Content-Type": "application/json"}
            data = {"username": LSA_USERNAME, "password": LSA_PASSWORD}
            response = requests.post(LSA_URL_LOGIN, json=data, headers=headers)
            response.raise_for_status()
            self._token = response.json()["access_token"]
            self._token_last_update = datetime.now()


MODEL_NAME = "AgentPublic/albertlight-7b"
API_URL = "https://albert.etalab.gouv.fr/api/v2"
TOKEN_DURATION = timedelta(hours=24)

class Albert_LLM(LLM):
    name: str = MODEL_NAME
    built_in_retriever: ClassVar[bool] = True
    _email = os.getenv("ALBERT_EMAIL")
    _username = os.getenv("ALBERT_USERNAME")
    _password = os.getenv("ALBERT_PASSWORD")
    _token = None
    _token_expiry = None
    _num_retries: int = 3
    _with_history: bool = False
    _chat_id: int = None

    def refresh_token(self):
        if self._token and self._token_expiry and datetime.now() < self._token_expiry:
            return

        data = {
            "email": self._email,
            "username": self._username,
            "password": self._password,
        }
        response = call_api(REQ_POST, f"{API_URL}/sign_in", json=data)
        self._token = response.json()["token"]
        self._token_expiry = datetime.now() + TOKEN_DURATION

    @property
    def headers(self):
        self.refresh_token()
        return {"Authorization": f"Bearer {self._token}"}

    def new_chat(self) -> int:
        data = {"chat_type": "qa"}
        response = call_api(REQ_POST, f"{API_URL}/chat", headers=self.headers, json=data)
        return response.json()["id"]

    def create_stream(self, query: str, limit: int = 7) -> int:
        data = {
            "query": query,
            "model_name": self.name,
            "mode": "rag",
            "with_history": self._with_history,
            "limit": limit,
        }
        
        if self._with_history:
            if not self._chat_id:
                self._chat_id = self.new_chat()
            url = f"{API_URL}/stream/chat/{self._chat_id}"
        else:
            url = f"{API_URL}/stream"
        
        response = call_api(REQ_POST, url, headers=self.headers, json=data)
        return response.json()["id"]

    def fetch_stream(self, stream_id: int) -> str:
        response = call_api(REQ_GET, f"{API_URL}/stream/{stream_id}/start", headers=self.headers, stream=True)

        answer = ""
        for line in response.iter_lines():
            if not line:
                continue

            decoded_line = line.decode("utf-8")
            _, _, data = decoded_line.partition("data: ")
            try:
                text = json.loads(data)
                if text == "[DONE]":
                    break
                answer += text
            except json.decoder.JSONDecodeError:
                print("\nDATA: " + data)
                print("\nERROR:")
                raise

        return answer

    def get_stream_data(self, stream_id: int):
        response = call_api(REQ_GET, f"{API_URL}/stream/{stream_id}", headers=self.headers)
        return response.json()

    def get_chunk_data(self, sheet_id: str):
        response = call_api(REQ_GET, f"{API_URL}/get_chunk/{sheet_id}", headers=self.headers)
        return response.json()

    async def complete(self, prompt: Prompt) -> LLMAnswer:
        retry: int = 1
        time_to_wait: float = 3.0
        result: str = ""
        while retry < self._num_retries:
            try :
                start_ts = datetime.now()
                
                stream_id = self.create_stream(query=prompt.user)
                result = self.fetch_stream(stream_id)
                
                stream_data = self.get_stream_data(stream_id)
                chunks = [self.get_chunk_data(sheet_id) for sheet_id in stream_data["rag_sources"]]
                break
            except Exception as e:
                await asyncio.sleep(time_to_wait)
                logger.debug(f"Excepton occured during api call, will retry 3 time each 3 second interval\nERROR:\n{e}")
                retry += 1
        duration = (datetime.now() - start_ts).total_seconds()
        return LLMAnswer(
            name=self.name,
            prompt=prompt,
            text=result,  # need refacto see albert doc,
            full_name=self.name,  # full name of the model?
            timestamp=start_ts,
            duration=duration,
            chunks=chunks
        )

        # return {
        #     "name": self.name,
        #     "prompt": prompt,
        #     "text": result,
        #     "full_name": self.name,
        #     "timestamp": start_ts,
        #     "duration": duration,
        #     "cost": 0.0,
        #     "stream_data": stream_data,
        #     "chunks": chunks
        # }

class EvalPrompterLSA(Prompter):
    """
    Prompt: FAITS and REPONSE - expect the REPONSE to be rewritten including the FACTS in the text
    Post_process: analyse cited factsfacts not cited, and facts invented (?)
    """

    system: str = """Vous devez comparer une liste numérotée de FAITS avec une REPONSE. Votre tâche consiste à évaluer la présence de chaque FAIT dans la REPONSE, en suivant ces règles :

Reproduire la REPONSE telle quelle, en insérant entre parenthèses le numéro de chaque FAIT dont l'idée principale est présente dans la REPONSE.
Si une phrase de la REPONSE correspond à plusieurs FAITS, indiquer les numéros de ces FAITS entre parenthèses, séparés par une virgule (ex : (1,2)).
Ne valider un FAIT que si toute son idée principale est clairement exprimée dans la REPONSE ou peut être déduite de la REPONSE dans son ensemble.
Si une partie de la REPONSE ne correspond à aucun FAIT, insérer un point d'interrogation entre parenthèses (?) à cet endroit.
Si une partie de la REPONSE fait référence à un emplacement dans un document (ex : page X), ne rien indiquer pour cette partie.

Quelques précisions :

Ne vous fiez pas à la formulation exacte des FAITS, mais concentrez-vous sur leurs idées principales.
Une idée peut être exprimée différemment dans la REPONSE par rapport aux FAITS, l'essentiel est que le sens soit le même.
Si une idée est sous-entendue ou peut être déduite de l'ensemble de la REPONSE, vous pouvez valider le FAIT correspondant.
        """

    def get_prompt(self, answer: Answer, facts: Facts) -> Prompt:
        result: Prompt = Prompt()
        facts_as_str: str = "\n".join(
            f"{i}. {fact.text}" for i, fact in enumerate(facts, start=1))
        result.user = f"-- FAITS --\n{facts_as_str}\n\n-- REPONSE --\n{answer.text}"
        result.system = self.system
        return result

    def post_process(self, qa: QA, cur_obj: Eval):
        answer: str = cur_obj.llm_answer.text if cur_obj.llm_answer.text != "[]" else ""
        # removes the word FAIT before the fact number as it is sometimes generated in the answer
        answer = answer.replace("(FAIT ", "(")
        # get the set of facts numbers from answer
        facts_in_answer: set[int] = set([int(s) for s in ",".join(re.findall(
            "\([\d+,+\s+]+\)", answer)).replace("(", "").replace(")", "").split(",") if s])
        # get the numbers in the true facts
        true_facts: set[int] = set(
            [int(s.text[0] if s.text[1] == "." else s.text[:2]) for s in qa.facts if s])
        true_facts_in_answer: set[int] = facts_in_answer & true_facts
        true_facts_not_in_answer: set[int] = true_facts - true_facts_in_answer
        # get the number of extra facts (?) - they are not always hallucinations, sometimes just true facts not interesting and not included as usefule facts
        nb_extra_facts_in_answer: int = len(re.findall("\(\?\)", answer))
        # compute metrics
        precision: float = div0(len(true_facts_in_answer), len(
            facts_in_answer) + nb_extra_facts_in_answer)
        recall: float = div0(len(true_facts_in_answer), len(true_facts))
        cur_obj.meta["precision"] = precision
        cur_obj.meta["recall"] = recall
        cur_obj.meta["extra"] = nb_extra_facts_in_answer
        cur_obj.meta["missing"] = ", ".join(
            str(v) for v in list(true_facts_not_in_answer))
        cur_obj.meta["nb_missing"] = len(true_facts_not_in_answer)
        cur_obj.meta["facts_in_ans"] = str(sorted(facts_in_answer))
        cur_obj.auto = div0(2 * precision * recall, precision + recall)
        cur_obj.text = answer


class EvalPrompterAlbert(Prompter):
    """
    Prompt: FAITS and REPONSE - expect the REPONSE to be rewritten including the FACTS in the text
    Post_process: analyse cited factsfacts not cited, and facts invented (?)
    """

    system: str = """
    For each fact in a list of FACTS, determine whether the fact is supported in the PARAGRAPH or not and return :
- [OK] if the fact is supported, [NOT FOUND] if it is not supported and [HALLU] if an opposite fact is supported
- the reason why you return OK, NOT FOUND or HALLU
- the part in the PARAGRAPH related to the reason
At the end of the answer, add "[EXTRA] = number of ideas found in the PARAGRAPH that don't match the factual ideas." An idea is considered as [EXTRA] if:
-Off topic
-It gives information different from the facts ideas.
-Undesired extra context.
Exemple :
-> Input :

FACTS :
1. L'algorithme de Metropolis-Hastings cherche à obtenir une chaîne de Markov.
2. Cette chaîne de Markov doit admettre g comme mesure invariante.
3. Z ne doit pas apparaître dans le noyau de transition de cette chaîne.

PARAGRAPH
L'algorithme de Metropolis-Hastings cherche à obtenir une chaîne de Markov qui admette g comme mesure invariante et telle que Z n'apparaisse pas dans le noyau de transition.
-> Output :
1.[OK] - The paragraph states that "L'algorithme de Metropolis-Hastings cherche à obtenir une chaîne de Markov" which supports the first fact. 
Part in the paragraph: "L'algorithme de Metropolis-Hastings cherche à obtenir une chaîne de Markov"

2.[OK] - The paragraph states that "Cette chaîne de Markov doit admettre g comme mesure invariante" which supports the second fact.
Part in the paragraph: "qui admette g comme mesure invariante"

3.[OK] - The paragraph states that "Z ne doit pas apparaître dans le noyau de transition" which supports the third fact.
Part in the paragraph: "et telle que Z n'apparaisse pas dans le noyau de transition."

[EXTRA] = 0
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
            [int(match) for match in re.findall(r'(\d+)\.\s*\[OK\]', answer)])
        hallus_in_answer: set[int] = set(
            [int(match) for match in re.findall(r'(\d+)\.\s*\[HALLU\]', answer)])
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


class EvalPrompterAlbertV2(Prompter):
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


class EvalPrompterAlbert_YN(Prompter):
    """
    Prompt: FAITS and REPONSE - expect the REPONSE to be rewritten including the FACTS in the text
    Post_process: analyse cited factsfacts not cited, and facts invented (?)
    """

    system: str = """
I'll give you the QUESTION, ANSWER_REF, and ANSWER. Your job is to compare if the ANSWER and the ANSWER_REF are similar and respond with "OUI" or "NON". Judge if the ANSWER presents:
- The same information as the ANSWER_REF.
- The same context as the ANSWER_REF.
You should respond only with "OUI" or "NON" and provide no additional text.
Example:
-> Output:
OUI
        """

    def get_prompt(self, question: Question, answer: Answer, answer_ref: str) -> Prompt:
        result: Prompt = Prompt()
        result.user = f"-- QUESTION --\n{question.text}\n\n-- ANSWER_REF --\n{answer_ref}\n\n-- ANSWER --\n{answer.text}"
        result.system = self.system
        return result

    def post_process(self, qa: QA, cur_obj: Eval):
        cur_obj.text = cur_obj.llm_answer.text
        if re.search(r'\b(oui|yes)\b', cur_obj.text, re.IGNORECASE):
            cur_obj.auto = 1
        else:
            cur_obj.auto = 0


class EvalPrompterAlbert_Score(Prompter):
    """
    Prompt: FAITS and REPONSE - expect the REPONSE to be rewritten including the FACTS in the text
    Post_process: analyse cited factsfacts not cited, and facts invented (?)
    """

    system: str = """
I'll give you the QUESTION, ANSWER_REF, and ANSWER. 

Your task is to judge the similarity between the ANSWER and the ANSWER_REF on a scale of 1 to 10. The final score should be the average of the individual criteria scores.

Use the following criteria to judge the similarity between the two answers:

- Does the ANSWER discuss the same subject as ANSWER_REF?
- Does the ANSWER present the same information as ANSWER_REF?
- Does the wording of the ANSWER resemble ANSWER_REF?

Provide a score for each criterion, then calculate and report the average score. You should respond only with the final score and nothing more.
Example:
-> Output:
6
        """

    def get_prompt(self, question: Question, answer: Answer, answer_ref: str) -> Prompt:
        result: Prompt = Prompt()
        result.user = f"-- QUESTION --\n{question.text}\n\n-- ANSWER_REF --\n{answer_ref}\n\n-- ANSWER --\n{answer.text}"
        result.system = self.system
        return result

    def post_process(self, qa: QA, cur_obj: Eval):
        cur_obj.text = cur_obj.llm_answer.text
        match = re.search(r"\s*(\d+(\.\d+)?)", cur_obj.text)

        if match:
            score = float(match.group(1))
            normalized_score = score / 10
            cur_obj.auto = normalized_score


class EvalPrompterChunks(Prompter):


    system: str = """
    Évaluez la pertinence et l'exactitude du CHUNK par rapport à la QUESTION et aux FAITS listés.
Pour chaque FAIT, déterminez :

1. Pertinence thématique [0-4] :
   0 - Hors sujet, aucun lien avec le fait
   1 - Sujet vaguement connexe, mais pas directement lié
   2 - Sujet connexe, aborde le thème général
   3 - Sujet directement lié, mais ne se concentre pas sur l'aspect spécifique du fait
   4 - Parfaitement aligné avec le sujet du fait

2. Présence de l'information [0-4] :
   0 - Information totalement absente
   1 - Information très vaguement évoquée ou pouvant être inférée indirectement
   2 - Information partiellement présente ou implicite
   3 - Information présente mais pas complète ou directe
   4 - Information complètement et explicitement présente

3. Exactitude [0-4] :
   0 - Le chunk présente des informations qui sont complètement erronées ou qui contredisent directement le fait énoncé.
   1 - La majorité de l'information fournie est inexacte, mais il peut y avoir un ou deux détails mineurs qui sont corrects ou partiellement corrects.
   2 - Environ la moitié de l'information est correcte, mais il y a des erreurs significatives ou des omissions qui altèrent sérieusement la compréhension du fait.
   3 - La plupart des éléments fournis sont exacts, mais il y a de légères erreurs, des imprécisions ou des omissions qui n'affectent pas fondamentalement la compréhension du fait.
   4 - Toutes les informations fournies sont exactes, complètes et alignées avec le fait énoncé, sans erreurs ni omissions notables.


Note : Si le chunk ne contient aucune information relative au fait, l'exactitude devrait être notée 0.

4. Contexte : Citez la partie pertinente du CHUNK (si applicable)

Fournissez également :
- Le nombre d'informations supplémentaires pertinentes dans le CHUNK [EXTRA]
- Une analyse critique détaillée de la pertinence et de l'utilité du chunk par rapport à la question et au fait.
- Évalue en profondeur comment le texte répond à la question et traite les faits. Souligne les nuances, les correspondances et les erreurs spécifiques aux faits avant de noter.
- Vous devez respecter impérativement le format de réponse, et ne pas générer un text ou une explication de plus.
- Vous devez impérativement donner l'évaluation sur tous les faits.

Format de réponse :
Analyse critique détaillée : [votre analyse]

[Fait 1]
Pertinence thématique : [score]
Présence de l'information : [score]
Exactitude : [score]
Contexte : "[citation]"

[Fait 2]
...

[EXTRA] : [nombre]
        """

    def get_prompt(self, question: Question, answer: Answer, facts: Facts) -> Prompt:
        result: Prompt = Prompt()
        facts_as_str: str = "\n".join(
            f"{i}. {fact.text}" for i, fact in enumerate(facts, start=1))
        result.user = f"-- QUESTION --\n{question.text}\n\n-- FAITS --\n{facts_as_str}\n\n-- CHUNK --\n{answer.text}"
        result.system = self.system
        return result

    def post_process(self, qa: QA, cur_obj: Eval):
        answer: str = cur_obj.llm_answer.text if cur_obj.llm_answer.text != "[]" else ""
        facts = re.findall(r"\[Fait \d+\]", answer)
        thematic_pertinence = re.findall(r"Pertinence thématique : (\d)", answer)
        presence_information = re.findall(r"Présence de l'information : (\d)", answer)
        accuracy_scores = re.findall(r"Exactitude : (\d)", answer)
        extra_score = re.findall(r"\[EXTRA\] : (\d)", answer)
        extra_text = re.findall(r"\[EXTRA\] : \d \((.+)\)", answer)
        cur_obj.text = markdown.markdown(answer)

class EvalPrompterChunksV2(Prompter):

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