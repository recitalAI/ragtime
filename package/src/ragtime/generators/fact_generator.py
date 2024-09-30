from ragtime.expe import StartFrom, QA, Answer, Facts
from ragtime.generators import TextGenerator
from ragtime.config import logger

class FactGenerator(TextGenerator):
    """
    Generate Facts from existing Answers
    """

    async def gen_for_qa(
        self,
        qa: QA,
        start_from: StartFrom = StartFrom.beginning,
        b_missing_only: bool = False,
        only_llms: list[str] = None,
    ):
        """
        Create Facts based on the first Answer in the QA having human Eval equals 1
        """

        ans: Answer = next((a for a in qa.answers if a.eval and a.eval.human == 1.0))
        if not ans:
            logger.debug(f"No fact has been generated since no answer has been validated (human=1.0) for this question")
            return

        model_str: str = (
            f" associated with answer from model {ans.llm_answer.full_name}"
            if ans.llm_answer
            else ""
        )
        logger.info(
            f"Generate Facts since it has a human validated answer (eval.human == 1.0){model_str}"
        )
        prev_facts: Facts = qa.facts

        # 2.a. and 2.b : prompt generation + Text generation with LLM
        qa.facts = await self.llm.generate(
            cur_obj=Facts(),
            prev_obj=prev_facts,
            qa=qa,
            start_from=start_from,
            b_missing_only=b_missing_only,
            question=qa.question,
            answer=ans,
        )
