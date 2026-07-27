import inspect
from ragtime.retrievers import Retriever
from ragtime.llms import LLM

def _all_subclasses(cls):
    """Every descendant of cls, not just direct children. __subclasses__()
    returns direct children only, so a model that subclasses LiteLLM or
    ReasoningLLM (rather than LLM directly) would otherwise be invisible."""
    result = set()
    for sub in cls.__subclasses__():
        result.add(sub)
        result |= _all_subclasses(sub)
    return result


def get_child_classes(parent_class):
    """Get all descendant classes defined in the app.services package
    (built-in models plus the user's mounted classes.py)."""
    return [cls for cls in _all_subclasses(parent_class)
            if cls.__module__.startswith('app.services')]

def get_retriever_classes():
    """Get all available retriever classes"""
    return get_child_classes(Retriever)

def get_llm_classes():
    """Get all available LLM classes"""
    return get_child_classes(LLM)

def get_llm_info():
    """Get detailed information about available LLM classes.

    provider / required_key / title / reasoning attrs are read from optional
    class attributes: the committed built-in models (builtin_llms.py) set them
    for first-class catalog treatment, while the user's own classes.py models
    fall back to the 'Customized' / no-key defaults, exactly as before."""
    llm_classes = get_llm_classes()

    def _model_string(cls):
        """The actual model string the class sends to the provider.

        On the package's pydantic LLM classes, `name` is a model *field*, so
        its value lives in model_fields[...].default rather than as a plain
        class attribute (getattr(cls, 'name') would miss it). Fall back to a
        plain attribute, then the class name, for non-pydantic customs."""
        try:
            fields = getattr(cls, 'model_fields', None)
            if fields and 'name' in fields:
                default = fields['name'].default
                if default:
                    return default
        except Exception:
            pass
        return getattr(cls, 'name', cls.__name__)

    return [{
        'name': cls.__name__,
        # The actual model string sent to the provider (e.g. OVH classes use
        # 'openai/gpt-oss-120b'); used to look up a price for the catalog tag
        # (feature 1).
        'model_name': _model_string(cls),
        'title': getattr(cls, 'title', cls.__name__),
        'provider': getattr(cls, 'provider', 'Customized'),
        'required_key': getattr(cls, 'required_key', None),
        'supports_reasoning_toggle': getattr(cls, 'supports_reasoning_toggle', False),
        'supports_reasoning_effort': getattr(cls, 'supports_reasoning_effort', False),
        'reasoning_note': getattr(cls, 'reasoning_note', None),
        'built_in_retriever': getattr(cls, 'built_in_retriever', False),
        'answer_gen_only': getattr(cls, 'answer_gen_only', False),
        'description': cls.__doc__ or 'No description available',
        'parameters': _get_init_parameters(cls)
    } for cls in llm_classes]


def _get_init_parameters(cls):
    """Extract initialization parameters from a class"""
    try:
        params = inspect.signature(cls.__init__).parameters
        return [{
            'name': name,
            'required': param.default == param.empty,
            'default': None if param.default == param.empty else param.default,
            'type': str(param.annotation) if param.annotation != param.empty else 'Any'
        } for name, param in params.items() if name != 'self']
    except:
        return []