import inspect
from ragtime.retrievers import Retriever
from ragtime.llms import LLM

def get_child_classes(parent_class):
    """Get all child classes of a parent class"""
    return [cls for cls in parent_class.__subclasses__() 
            if cls.__module__.startswith('app.services')]

def get_retriever_classes():
    """Get all available retriever classes"""
    return get_child_classes(Retriever)

def get_llm_classes():
    """Get all available LLM classes"""
    return get_child_classes(LLM)

def get_llm_info():
    """Get detailed information about available LLM classes"""
    llm_classes = get_llm_classes()
    return [{
        'name': cls.__name__,
        'built_in_retriever': getattr(cls, 'built_in_retriever', False),
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