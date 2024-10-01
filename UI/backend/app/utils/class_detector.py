import inspect
from ragtime.retrievers import Retriever
from ragtime.llms import LLM

def get_child_classes(parent_class):
    return [cls for cls in parent_class.__subclasses__() if cls.__module__.startswith('app.services')]

def get_retriever_classes():
    return get_child_classes(Retriever)

def get_llm_classes():
    return get_child_classes(LLM)

def get_llm_info():
    llm_classes = get_llm_classes()
    return [{
        'name': cls.__name__,
        'built_in_retriever': getattr(cls, 'built_in_retriever', False)
    } for cls in llm_classes]