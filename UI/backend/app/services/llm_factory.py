"""Build the right LLM object for a model name.

The frozen package turns a bare model-name string into a plain LiteLLM
(text_generator.py: `LiteLLM(name=llm, prompter=prompter)`), which means a
reasoning model used as a JUDGE (eval) or for FACT generation would get:
  - no reasoning-content handling, and
  - the default max_tokens=2000 shared between hidden reasoning and visible
    output -> the model spends the budget thinking and returns EMPTY text.
For eval that shows up as every fact scored "missing" (nb_ok=0, auto=0);
for fact generation as no facts at all.

So our services build the LLM object themselves and pass the OBJECT to the
generators (the package accepts LLM instances as well as strings).
"""
from ragtime.llms import LiteLLM, ReasoningLLM

from app.services.model_meta import reasoning_meta_for
from app.utils.class_detector import get_llm_classes


def build_llm(model_name: str, prompter, reasoning: bool = None):
    """Return an LLM instance for `model_name` with the given prompter.

    - custom/built-in classes (e.g. OVH) -> that class
    - catalog reasoning string models (gpt-5, o4-mini, opus) -> ReasoningLLM
    - anything else -> plain LiteLLM (unchanged behavior)
    """
    llm_class = next((c for c in get_llm_classes() if c.__name__ == model_name), None)
    if llm_class:
        kwargs = {}
        if reasoning is not None and issubclass(llm_class, ReasoningLLM):
            kwargs['reasoning'] = reasoning
        return llm_class(prompter=prompter, **kwargs)

    meta = reasoning_meta_for(model_name)
    if meta:
        kwargs = {'name': model_name, 'prompter': prompter}
        if meta.get('toggle_style'):
            kwargs['reasoning_toggle_style'] = meta['toggle_style']
            if reasoning is not None:
                kwargs['reasoning'] = reasoning
        return ReasoningLLM(**kwargs)

    return LiteLLM(name=model_name, prompter=prompter)
