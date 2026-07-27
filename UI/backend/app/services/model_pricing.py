"""Resolve a per-model price (USD per 1M tokens) for the model catalog, so the
UI can show a rough cost tag next to each model in the selectors (feature 1).

Two sources, already present in the app — nothing new is priced here:
  - OVH models: OVH_PRICES_PER_M in ovh_pricing.py (our own table).
  - Everyone else (OpenAI / Anthropic / Mistral): LiteLLM's built-in price map
    (litellm.model_cost), the same table completion_cost() uses at runtime.

LiteLLM keys some models without the provider prefix (e.g. it has
`claude-opus-4-8` but not `anthropic/claude-opus-4-8`, and `gpt-5.4` but the
catalog may send `gpt-5.4`). We therefore try the exact name, then the name
with its first `provider/` segment stripped — the same bare/prefixed dance
ovh_pricing.py already does when registering.

Everything is best-effort: if a price can't be found, we return None and the UI
simply shows no tag. Pricing must never affect answers, evals, or startup.
"""
import logging

from app.services.ovh_pricing import OVH_PRICES_PER_M


def _litellm_price_per_m(model_name):
    """(input, output) USD per 1M tokens from LiteLLM's map, or None."""
    try:
        import litellm
    except ImportError:  # pragma: no cover
        return None

    cost_map = getattr(litellm, 'model_cost', {}) or {}
    candidates = [model_name]
    if '/' in model_name:
        # Strip the leading provider segment: anthropic/claude-opus-4-8 ->
        # claude-opus-4-8 (LiteLLM often keys the bare name).
        candidates.append(model_name.split('/', 1)[1])

    for key in candidates:
        entry = cost_map.get(key)
        if not entry:
            continue
        in_tok = entry.get('input_cost_per_token')
        out_tok = entry.get('output_cost_per_token')
        if in_tok is None and out_tok is None:
            continue
        return (
            (in_tok or 0.0) * 1_000_000,
            (out_tok or 0.0) * 1_000_000,
        )
    return None


def _ovh_price_per_m(model_name):
    """(input, output) USD per 1M tokens for an OVH model, or None.

    OVH catalog names come through as the class .name, which may be the bare
    model id or `openai/<id>`. OVH_PRICES_PER_M is keyed by the bare id.
    """
    bare = model_name.split('/', 1)[1] if '/' in model_name else model_name
    for key in (model_name, bare):
        if key in OVH_PRICES_PER_M:
            return OVH_PRICES_PER_M[key]
    return None


def price_per_m(model_name, provider=None):
    """Return {'input': x, 'output': y} in USD per 1M tokens, or None.

    OVH models are looked up in our own table first (their LiteLLM entries are
    registered under `openai/<id>` and would otherwise collide); everything
    else uses LiteLLM's map.
    """
    if not model_name:
        return None
    try:
        prov = (provider or '').lower()
        found = None
        if prov == 'ovh':
            found = _ovh_price_per_m(model_name)
        if found is None:
            found = _litellm_price_per_m(model_name)
        if found is None and prov != 'ovh':
            # Last resort for oddly-named OVH-like models.
            found = _ovh_price_per_m(model_name)
        if found is None:
            return None
        return {'input': round(found[0], 4), 'output': round(found[1], 4)}
    except Exception as e:  # never let pricing break the catalog
        logging.debug(f"price_per_m failed for {model_name}: {e}")
        return None
