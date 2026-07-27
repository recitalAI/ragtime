from flask import Blueprint, jsonify

# Importing these registers LLM/retriever subclasses so class_detector can
# discover them:
#   - builtin_llms: committed first-class models shipped with the product
#     (OVH). They carry provider/required_key class attrs -> get_llm_info
#     surfaces them and they are gated on their key like the entries below.
#   - classes: the user's docker-mounted extension point (own/open-source
#     models); discovered as provider "Customized" with no key gating.
import app.services.builtin_llms  # noqa: F401
try:
    import app.services.classes  # noqa: F401  (user extension point; optional mount)
except ImportError:
    pass  # no user classes.py mounted — fine

from app.utils.class_detector import get_llm_info, get_retriever_classes
from app.services.model_pricing import price_per_m

models_info_bp = Blueprint('models_info', __name__, url_prefix='/api')

# Built-in LiteLLM model catalog for cloud providers reached by model string
# (single source of truth; sub-step 5.3 moved this off the frontend).
# `required_key` matches /api/user/api-keys/availability so the UI disables a
# model when its key is missing. `reasoning` marks models whose thinking must
# be handled specially (ReasoningLLM in the package); `supports_reasoning_toggle`
# and `reasoning_note` drive the per-model reasoning control in the UI.
#
# OVH models are NOT here — they need api_base/credentials, so they are Python
# classes in builtin_llms.py, surfaced through get_llm_info below.
BUILTIN_MODELS = [
    # OpenAI
    {'name': 'gpt-5', 'title': 'GPT-5', 'provider': 'OpenAI', 'required_key': 'openai',
     'reasoning': True, 'supports_reasoning_toggle': False, 'supports_reasoning_effort': True,
     'reasoning_note': 'Reasoning always on (effort configurable)'},
    # gpt-5.4 / 5.5 / 5.6 are answer-generation only for now (feature 3): they
    # are offered in the experiment-setup answer-gen grid. The validation-set
    # screens keep their existing, smaller model list. Marked as reasoning
    # models with a configurable effort level, like gpt-5.
    {'name': 'gpt-5.4', 'title': 'GPT-5.4', 'provider': 'OpenAI', 'required_key': 'openai',
     'answer_gen_only': True, 'reasoning': True, 'supports_reasoning_toggle': False,
     'supports_reasoning_effort': True, 'reasoning_note': 'Reasoning always on (effort configurable)'},
    {'name': 'gpt-5.5', 'title': 'GPT-5.5', 'provider': 'OpenAI', 'required_key': 'openai',
     'answer_gen_only': True, 'reasoning': True, 'supports_reasoning_toggle': False,
     'supports_reasoning_effort': True, 'reasoning_note': 'Reasoning always on (effort configurable)'},
    {'name': 'gpt-5.6', 'title': 'GPT-5.6', 'provider': 'OpenAI', 'required_key': 'openai',
     'answer_gen_only': True, 'reasoning': True, 'supports_reasoning_toggle': False,
     'supports_reasoning_effort': True, 'reasoning_note': 'Reasoning always on (effort configurable)'},
    {'name': 'gpt-4o', 'title': 'GPT-4o', 'provider': 'OpenAI', 'required_key': 'openai'},
    {'name': 'o4-mini', 'title': 'o4-mini', 'provider': 'OpenAI', 'required_key': 'openai',
     'reasoning': True, 'supports_reasoning_toggle': False, 'supports_reasoning_effort': True,
     'reasoning_note': 'Reasoning always on (effort configurable)'},
    # Anthropic
    {'name': 'anthropic/claude-opus-4-8', 'title': 'Claude Opus 4.8', 'provider': 'Anthropic',
     'required_key': 'anthropic', 'reasoning': True, 'supports_reasoning_toggle': True,
     'supports_reasoning_effort': True},
    # New Anthropic models — answer-generation only for now (feature 3).
    {'name': 'anthropic/claude-opus-4-7', 'title': 'Claude Opus 4.7', 'provider': 'Anthropic',
     'required_key': 'anthropic', 'answer_gen_only': True, 'reasoning': True,
     'supports_reasoning_toggle': True, 'supports_reasoning_effort': True},
    {'name': 'anthropic/claude-sonnet-4-6', 'title': 'Claude Sonnet 4.6', 'provider': 'Anthropic',
     'required_key': 'anthropic', 'answer_gen_only': True, 'reasoning': True,
     'supports_reasoning_toggle': True, 'supports_reasoning_effort': True},
    {'name': 'anthropic/claude-sonnet-4-5', 'title': 'Claude Sonnet 4.5', 'provider': 'Anthropic',
     'required_key': 'anthropic', 'answer_gen_only': True, 'reasoning': True,
     'supports_reasoning_toggle': True, 'supports_reasoning_effort': True},
    {'name': 'anthropic/claude-haiku-4-5', 'title': 'Claude Haiku 4.5', 'provider': 'Anthropic',
     'required_key': 'anthropic', 'answer_gen_only': True},
    # Mistral
    {'name': 'mistral/mistral-large-latest', 'title': 'Mistral Large', 'provider': 'Mistral AI', 'required_key': 'mistral'},
    {'name': 'mistral/mistral-medium-latest', 'title': 'Mistral Medium', 'provider': 'Mistral AI', 'required_key': 'mistral'},
    {'name': 'mistral/mistral-small-latest', 'title': 'Mistral Small', 'provider': 'Mistral AI', 'required_key': 'mistral'},
]

# Providers that gate on an API key, derived from the catalog + built-in
# classes so a new provider needs no change to the availability endpoint.
_STATIC_KEYS = {m['required_key'] for m in BUILTIN_MODELS if m.get('required_key')}


def _model_defaults(model):
    """Fill catalog rows with the reasoning fields so the response shape is
    uniform whether or not a row set them."""
    return {
        'reasoning': False,
        'supports_reasoning_toggle': False,
        'supports_reasoning_effort': False,
        'reasoning_note': None,
        'built_in_retriever': False,
        'custom': False,
        'answer_gen_only': False,
        'pricing': None,
        **model,
    }


@models_info_bp.route('/available-models', methods=['GET'])
def get_available_models():
    """Unified model catalog: cloud built-ins (BUILTIN_MODELS) + discovered
    classes (committed OVH built-ins with real provider/key, plus the user's
    Customized models). Additive, uniform shape."""
    models = [_model_defaults(m) for m in BUILTIN_MODELS]
    for m in models:
        # Rough price tag (USD per 1M tokens) for the selector (feature 1).
        if m.get('pricing') is None:
            m['pricing'] = price_per_m(m['name'], m.get('provider'))
    for info in get_llm_info():
        is_custom = info.get('provider', 'Customized') == 'Customized'
        models.append({
            'name': info['name'],
            'title': info.get('title', info['name']),
            'provider': info.get('provider', 'Customized'),
            'required_key': info.get('required_key'),
            'reasoning': bool(info.get('reasoning_note') or info.get('supports_reasoning_toggle')),
            'supports_reasoning_toggle': info.get('supports_reasoning_toggle', False),
            'supports_reasoning_effort': info.get('supports_reasoning_effort', False),
            'reasoning_note': info.get('reasoning_note'),
            'built_in_retriever': info.get('built_in_retriever', False),
            'custom': is_custom,
            'answer_gen_only': info.get('answer_gen_only', False),
            # OVH classes carry provider 'OVH' -> priced from OVH_PRICES_PER_M
            # via the runtime model string (info['model_name'], e.g.
            # 'openai/gpt-oss-120b'); customs usually have no known price.
            'pricing': price_per_m(info.get('model_name', info['name']), info.get('provider')),
        })
    return jsonify(models)


@models_info_bp.route('/available-retrievers', methods=['GET'])
def get_available_retrievers():
    retriever_classes = get_retriever_classes()
    return jsonify([cls.__name__ for cls in retriever_classes])


def required_keys():
    """All provider keys that gate a model: the static cloud catalog plus any
    required_key declared by a discovered built-in class (e.g. OVH)."""
    keys = set(_STATIC_KEYS)
    for info in get_llm_info():
        rk = info.get('required_key')
        if rk:
            keys.add(rk)
    return keys
