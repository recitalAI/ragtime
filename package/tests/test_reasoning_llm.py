"""Regression tests for reasoning-model answer capture.

Reasoning models emit chain-of-thought that must not reach the prompters'
post_process (which parse llm_answer.text). These tests reproduce the
"garbage facts / No Answers" corruption on the old LiteLLM path and prove the
ReasoningLLM / ThinkTagReasoningLLM classes fix it, against the four prompters
the interface actually uses. No network / API keys required (acompletion is
monkeypatched).
"""
import asyncio
import warnings

warnings.filterwarnings("ignore")

import ragtime.llms.llm as llmmod
from ragtime.llms import LiteLLM, ReasoningLLM, ThinkTagReasoningLLM
from ragtime.expe import Prompt, Answer, Facts, Eval, QA, Question, Fact
from ragtime.prompters.fact_prompters import FactPrompterFR_2024_06_04
from ragtime.prompters.answer_prompters import AnsPrompterBase
from ragtime.prompters.eval_prompters import EvalPrompterFRV2

llmmod.completion_cost = lambda a: 0.0

LEAK = (
    "<think>\nOkay, the user wants short factual sentences.\n"
    "Let me identify the key facts. First, the cat is black.\n"
    "Also it sleeps.\n</think>\n1. Le chat est noir\n2. Le chat dort"
)


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _patch(content, reasoning_content=None):
    async def fake(**kw):
        msg = {"content": content, "role": "assistant"}
        if reasoning_content is not None:
            msg["reasoning_content"] = reasoning_content
        return {"model": "m", "choices": [{"message": msg}]}
    llmmod.acompletion = fake


def test_old_path_corrupts_facts_on_think_leak():
    _patch(LEAK)
    m = LiteLLM(name="x", prompter=FactPrompterFR_2024_06_04(), num_retries=3)
    la = _run(m.complete(Prompt(user="p", system="s")))
    facts = Facts(); facts.llm_answer = la
    FactPrompterFR_2024_06_04().post_process(QA(question=Question(text="q")), facts)
    assert len(facts.items) > 2  # bug: reasoning becomes garbage facts


def test_thinktag_strips_leak_and_facts_are_clean():
    _patch(LEAK)
    m = ThinkTagReasoningLLM(name="x", prompter=FactPrompterFR_2024_06_04(), num_retries=3)
    la = _run(m.complete(Prompt(user="p", system="s")))
    assert "<think>" not in la.text
    facts = Facts(); facts.llm_answer = la
    FactPrompterFR_2024_06_04().post_process(QA(question=Question(text="q")), facts)
    assert [f.text for f in facts.items] == ["1. Le chat est noir", "2. Le chat dort"]


def test_reasoning_content_kept_in_meta():
    _patch("1. Le chat est noir\n2. Le chat dort", reasoning_content="my thinking")
    m = ReasoningLLM(name="x", prompter=FactPrompterFR_2024_06_04(), num_retries=3)
    la = _run(m.complete(Prompt(user="p", system="s")))
    assert la.meta.get("reasoning_content") == "my thinking"
    assert "thinking" not in la.text


def test_answer_text_is_final_only():
    _patch("Paris est la capitale.", reasoning_content="user asks the capital")
    m = ReasoningLLM(name="x", prompter=AnsPrompterBase(), num_retries=3)
    la = _run(m.complete(Prompt(user="p", system="s")))
    ans = Answer(); ans.llm_answer = la
    AnsPrompterBase().post_process(QA(question=Question(text="q")), ans)
    assert "Paris" in ans.text and "user asks" not in ans.text.lower()


def test_eval_counts_ignore_thinking():
    _patch("1. [OK]\n2. [HALLU]\n[EXTRA] = 0",
           reasoning_content="3. [OK] maybe? Fact 2 is HALLU probably.")
    qa = QA(question=Question(text="q"))
    qa.facts.items = [Fact(text="1. a"), Fact(text="2. b")]
    m = ReasoningLLM(name="x", prompter=EvalPrompterFRV2(), num_retries=3)
    la = _run(m.complete(Prompt(user="p", system="s")))
    ev = Eval(); ev.llm_answer = la
    EvalPrompterFRV2().post_process(qa, ev)
    assert ev.meta["nb_ok"] == 1 and ev.meta["nb_hallu"] == 1


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn(); print("PASS", name)
