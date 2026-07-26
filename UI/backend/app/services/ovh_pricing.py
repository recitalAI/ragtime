"""Register OVH model prices with LiteLLM so cost is computed instead of 0.

Why this is needed: our OVH classes address the endpoint as
`openai/<model>` + api_base (OpenAI-compatible route). LiteLLM's price table
has no entry for those names, so completion_cost() raises
"This model isn't mapped yet" and cost falls back to 0.

litellm.register_model() adds entries to that table at runtime, keyed by the
exact model string we send. Prices are USD per token (LiteLLM's unit), i.e.
USD-per-million / 1e6.

Rates below are OVH AI Endpoints public per-token pricing (USD/1M tokens).
They change: keep them here, in one place, and update as needed. If a model is
missing or a price is wrong, cost simply reads 0 again -- answers and
evaluations are never affected.
"""
import contextlib
import io
import logging

# USD per 1M tokens: (input, output)
OVH_PRICES_PER_M = {
    "Mistral-7B-Instruct-v0.3": (0.10, 0.10),
    "Mistral-Nemo-Instruct-2407": (0.13, 0.13),
    "Meta-Llama-3_3-70B-Instruct": (0.67, 0.67),
    "Qwen3-32B": (0.08, 0.23),
    "gpt-oss-20b": (0.04, 0.15),
    "gpt-oss-120b": (0.08, 0.45),
}


def register_ovh_prices():
    """Register OVH per-token prices with LiteLLM. Safe to call repeatedly."""
    try:
        import litellm
    except ImportError:  # pragma: no cover
        return

    entries = {}
    for model, (in_price, out_price) in OVH_PRICES_PER_M.items():
        entries[f"openai/{model}"] = {
            "input_cost_per_token": in_price / 1_000_000,
            "output_cost_per_token": out_price / 1_000_000,
            "litellm_provider": "openai",
            "mode": "chat",
        }
        # The response's `model` field often comes back without the prefix,
        # so register the bare name too.
        entries[model] = {
            "input_cost_per_token": in_price / 1_000_000,
            "output_cost_per_token": out_price / 1_000_000,
            "litellm_provider": "openai",
            "mode": "chat",
        }
    try:
        # register_model is noisy for models absent from the built-in cost map:
        # it warns about cache-cost fields AND prints a red "Provider List: ..."
        # banner straight to stdout (not through logging). Both are harmless
        # here, so silence the logger AND capture stdout/stderr for the call.
        litellm_logger = logging.getLogger("LiteLLM")
        prev_level = litellm_logger.level
        litellm_logger.setLevel(logging.ERROR)
        try:
            with contextlib.redirect_stdout(io.StringIO()), \
                 contextlib.redirect_stderr(io.StringIO()):
                litellm.register_model(entries)
        finally:
            litellm_logger.setLevel(prev_level)
        logging.info(f"Registered OVH pricing for {len(OVH_PRICES_PER_M)} models")
    except Exception as e:  # never let pricing break startup
        logging.warning(f"Could not register OVH pricing: {e}")
