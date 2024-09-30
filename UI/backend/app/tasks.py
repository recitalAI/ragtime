import os
from ragtime.expe import Expe, QA, Question, Answer
from ragtime.generators import AnsGenerator, FactGenerator, EvalGenerator, EvalGeneratorChunks
from ragtime.prompters import AnsPrompterBase, FactPrompterJazz
from ragtime.llms import LiteLLM
from app.services.classes import EvalPrompterAlbertV2, EvalPrompterChunksV2, Albert_LLM
from config import Config

def generate_answers_task(input_queue, output_queue):
    while True:
        data = input_queue.get()
        if data is None:  # This is our signal to stop the process
            break

        expe = Expe()
        for item in data['items']:
            qa = QA(question=Question(text=item['question']['text']))
            expe.append(qa)

        prompter = AnsPrompterBase()
        api_key = Config.get_openai_api_key()
        answer_generator = AnsGenerator(llms=[LiteLLM(name='gpt-4', prompter=prompter, api_key=api_key)])

        try:
            answer_generator.generate(expe=expe)
            result = [
                {
                    'question': qa.question.model_dump(),
                    'answers': [answer.model_dump() for answer in qa.answers]
                } for qa in expe
            ]
            output_queue.put(('success', result))
        except Exception as e:
            output_queue.put(('error', str(e)))

def generate_facts_task(input_queue, output_queue):
    while True:
        data = input_queue.get()
        if data is None:  # This is our signal to stop the process
            break

        expe = Expe()
        for item in data['items']:
            qa = QA(question=Question(text=item['question']['text']))
            if 'answers' in item and 'items' in item['answers']:
                qa.answers.items = [Answer(**a) for a in item['answers']['items']]
            expe.append(qa)

        prompter = FactPrompterJazz()
        api_key = Config.get_openai_api_key()
        fact_generator = FactGenerator(llms=[LiteLLM(name='gpt-4', prompter=prompter, api_key=api_key)])

        try:
            fact_generator.generate(expe=expe)
            result = [
                {
                    'question': qa.question.model_dump(),
                    'facts': qa.facts.model_dump() if qa.facts else None
                } for qa in expe
            ]
            output_queue.put(('success', result))
        except Exception as e:
            output_queue.put(('error', str(e)))



def generate_evals_task(input_queue, output_queue):
    while True:
        data = input_queue.get()
        if data is None:  # This is our signal to stop the process
            break

        try:
            expe = Expe(**data['expe'])
            evaluation_model = data['evaluation_model']
            evaluate_answers = data['evaluate_answers']
            evaluate_chunks = data['evaluate_chunks']

            answer_prompter = EvalPrompterAlbertV2()
            chunk_prompter = EvalPrompterChunksV2()

            if evaluation_model == 'albert':
                model = Albert_LLM()
            else:
                model = LiteLLM(name=evaluation_model, api_key=Config.get_openai_api_key())

            if evaluate_answers:
                eval_gen = EvalGenerator(llms=[model], prompter=answer_prompter)
                eval_gen.generate(expe=expe)

            if evaluate_chunks:
                chunk_eval_gen = EvalGeneratorChunks(llms=[model], prompter=chunk_prompter)
                chunk_eval_gen.generate(expe=expe)

            output_queue.put(('success', expe.model_dump()))
        except Exception as e:
            output_queue.put(('error', str(e)))