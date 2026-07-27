"""Reasoning metadata for cloud string models (those in BUILTIN_MODELS reached
by model string, not by a Python class). Lets the generators build a
ReasoningLLM with the right toggle style for models like gpt-5, o4-mini and
claude-opus-4-8 instead of a plain LiteLLM (which would drop the reasoning
handling and any thinking toggle).
"""

# model name -> {'toggle_style': 'anthropic'|'chat_template'|None}
# toggle_style None = reasoning always on, no per-request switch.
_REASONING_STRING_MODELS = {
    'gpt-5': {'toggle_style': None},
    'gpt-5.4': {'toggle_style': None},
    'gpt-5.5': {'toggle_style': None},
    'gpt-5.6': {'toggle_style': None},
    'o4-mini': {'toggle_style': None},
    'anthropic/claude-opus-4-8': {'toggle_style': 'anthropic'},
    'anthropic/claude-opus-4-7': {'toggle_style': 'anthropic'},
    'anthropic/claude-sonnet-4-6': {'toggle_style': 'anthropic'},
    'anthropic/claude-sonnet-4-5': {'toggle_style': 'anthropic'},
    # claude-haiku-4-5 is offered as a plain (non-reasoning) model, so it is
    # intentionally not listed here — it builds as a plain LiteLLM.
}


def reasoning_meta_for(model_name):
    """Return reasoning metadata for a string model, or None if it is not a
    reasoning model."""
    return _REASONING_STRING_MODELS.get(model_name)
