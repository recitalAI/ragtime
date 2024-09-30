from ragtime.generators.text_generator import *
from ragtime.llms import LLM
from ragtime.expe import StartFrom, QA, Eval, Facts, Answer
from ragtime.base import RagtimeException
from ragtime.config import logger, UNKNOWN_LLM


class EvalGenerator(TextGenerator):
    """
    Generate Eval from Answers and Facts.
    For a given QA, send the Answer and the Facts to the LLM to get the prompt back
    The default prompt returns all the valid facts given an answer, i.e. 1 prompt -> 1 Eval
    That could be overridden to have e.g. 1 prompt per Fact, i.e. N prompt -> 1 Eval
    The conversion between the LLM answer and the Eval is made in post_process
    """

    async def gen_for_qa(
        self,
        qa: QA,
        start_from: StartFrom = StartFrom.beginning,
        b_missing_only: bool = False,
        only_llms: list[str] = None,
    ):
        """
        Create Eval for each QA where Facts are available
        """

        if len(qa.answers) == 0:
            logger.error(f"No Answers, cannot generate Evals")
            return
        if len(qa.facts) == 0:
            logger.error(f"No Facts, cannot generate Evals")
            return

        # Eval loop
        for ans in (a for a in qa.answers if a.text):
            llm_name: str = ans.llm_answer.name if ans.llm_answer else UNKNOWN_LLM
            if only_llms and llm_name not in only_llms and llm_name != UNKNOWN_LLM:
                continue
            logger.debug(f'Generate Eval for answer generated with "{llm_name}"')
            prev_eval: Eval = ans.eval

            # 2.a. and 2.b : prompt generation + Text generation with LLM
            ans.eval = await self.llm.generate(
                cur_obj=Eval(),
                prev_obj=prev_eval,
                qa=qa,
                start_from=start_from,
                b_missing_only=b_missing_only,
                answer=ans,
                facts=qa.facts,
            )

            # save previous human eval if any
            if prev_eval and prev_eval.human:
                ans.eval.human = prev_eval.human


class TwoFactsEvalGenerator(TextGenerator):
    """
    Generate Eval from Answers and Facts. Converts first the Answer to a list of Facts and
    perform evaluation
    """

    def __init__(self, llms: list[LLM] = None):
        super().__init__(llms=llms)
        if len(self.llms) < 2:
            raise RagtimeException(
                """Need at least 2 LLMs to run this generator!
                                   1st LLM is used to generate Facts from the Answer.
                                   2nd LLM is used to generate Eval from the golden Facts and the Facts from the Answer."""
            )

    async def gen_for_qa(
        self,
        qa: QA,
        start_from: StartFrom = StartFrom.beginning,
        b_missing_only: bool = False,
    ):
        """
        Create Eval for each QA where Facts are available
        """

        if len(qa.answers) == 0:
            logger.error(f"No Answers, cannot generate Evals")
            return
        if len(qa.facts) == 0:
            logger.error(f"No Facts, cannot generate Evals")
            return

        # Eval loop
        for ans in (a for a in qa.answers if a.text):
            llm_name: str = (ans.llm_answer.name if ans.llm_answer else "unkown LLM (manual ?)")
            logger.debug(f'Generate Facts for answer generated with "{llm_name}"')
            prev_eval: Eval = ans.eval

            # Use 1st LLM to generate facts from the Answer
            ans_facts: Facts = await self.llms[0].generate(
                cur_obj=Facts(),
                prev_obj=None,
                qa=qa,
                start_from=start_from,
                b_missing_only=b_missing_only,
                answer=ans,
            )

            # Use 2nd LLM to generate Eval
            logger.debug(f"Then generate Eval using answer facts and gold facts")
            cur_eval: Eval = Eval()
            # stores the answer's facts in the current eval
            cur_eval.meta["answer_facts"] = [af.text for af in ans_facts]
            ans.eval = await self.llms[1].generate(
                cur_obj=cur_eval,
                prev_obj=prev_eval,
                qa=qa,
                start_from=start_from,
                b_missing_only=b_missing_only,
                answer_facts=ans_facts,
                gold_facts=qa.facts,
            )

            # save previous human eval if any
            if prev_eval and prev_eval.human:
                ans.eval.human = prev_eval.human


class EvalGeneratorChunks(TextGenerator):
    """
    Generate Eval from Answers and Facts.
    For a given QA, send the Answer and the Facts to the LLM to get the prompt back
    The default prompt returns all the valid facts given an answer, i.e. 1 prompt -> 1 Eval
    That could be overridden to have e.g. 1 prompt per Fact, i.e. N prompt -> 1 Eval
    The conversion between the LLM answer and the Eval is made in post_process
    """

    async def gen_for_qa(
        self,
        qa: QA,
        start_from: StartFrom = StartFrom.beginning,
        b_missing_only: bool = False,
        only_llms: list[str] = None,
    ):
        """
        Create Eval for each QA where Facts are available
        """

        if len(qa.chunks) == 0:
            logger.error(f"No chunks, cannot generate Evals")
            return
        if len(qa.facts) == 0:
            logger.error(f"No Facts, cannot generate Evals")
            return
        facts = qa.facts.items
        ans = qa.answers.items[0]
        if ans.eval.meta["nb_hallu"] == 0:
            logger.error(f"No Hallucination fact was detected")
        if ans.eval.meta["nb_missing"] == 0:
            logger.error(f"No Missing fact was detected")
        if ans.eval.meta["nb_hallu"] == 0 and ans.eval.meta["nb_missing"] == 0:
            return
        facts_hallu = []
        facts_missing = []
        for elem in ans.eval.meta["hallu"]:
            facts_hallu.append(qa.facts.items[int(elem)-1])
        for elem in ans.eval.meta["missing"]:
            facts_missing.append(qa.facts.items[int(elem)-1])
        if len(facts_hallu) != 0:
            ans = Answer()
            logger.debug(f'Generate Eval for hallucination found in the answer of the question "{qa.question.text}"')
            prev_eval: Eval = ans.eval
            # 2.a. and 2.b : prompt generation + Text generation with LLM
            ans.eval = await self.llm.generate(
                cur_obj=Eval(),
                prev_obj=prev_eval,
                qa=qa,
                start_from=start_from,
                b_missing_only=b_missing_only,
                question=qa.question,
                facts=facts_hallu,
                chunks=qa.chunks,
            )
            ans.llm_answer = {"name": "Hallucinations Eval",
                                         "full_name": "Hallucinations Eval"}
            # save previous human eval if any
            if prev_eval and prev_eval.human:
                ans.eval.human = prev_eval.human
            qa.answers.append(ans)
        if len(facts_missing) != 0:
            ans = Answer()
            logger.debug(f'Generate Eval for the missing facts for the question "{qa.question.text}"')
            prev_eval: Eval = ans.eval
            # 2.a. and 2.b : prompt generation + Text generation with LLM
            ans.eval = await self.llm.generate(
                cur_obj=Eval(),
                prev_obj=prev_eval,
                qa=qa,
                start_from=start_from,
                b_missing_only=b_missing_only,
                question=qa.question,
                facts=facts_missing,
                chunks=qa.chunks,
            )
            ans.llm_answer = {"name": "Missings Eval",
                                         "full_name": "Missings Eval"}
            # save previous human eval if any
            if prev_eval and prev_eval.human:
                ans.eval.human = prev_eval.human
            qa.answers.append(ans)

