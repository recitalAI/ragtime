from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import request, jsonify
from marshmallow import ValidationError
from .models.experiment_models import *
import os
import json
import logging
from datetime import datetime
from app.routes import EVALS_FOLDER
from app.services.answer_generator import AnswerGeneratorService
from app.services.evaluation_service import EvaluationService
from ragtime.prompters import AnsPrompterBase, AnsPrompterWithRetrieverFR
from ragtime.expe import Expe, QA, Question, Facts, Fact, Answers, Answer, LLMAnswer, Prompt
from app.utils.class_detector import get_retriever_classes, get_llm_info

experiment_bp = Blueprint('experiment_api', 'Experiment operations', url_prefix='/api')

@experiment_bp.route('/experiments')
class Experiments(MethodView):
    @experiment_bp.response(200, ExperimentListSchema(many=True))
    def get(self):
        """Get all experiments
        
        Returns a list of all experiments with their metadata and basic statistics.
        """
        try:
            experiments = []
            if not os.path.exists(EVALS_FOLDER):
                return []

            for filename in os.listdir(EVALS_FOLDER):
                if not filename.endswith('.json'):
                    continue

                file_path = os.path.join(EVALS_FOLDER, filename)
                with open(file_path, 'r') as f:
                    data = json.load(f)

                total_chunks = sum(len(qa.get('chunks', {}).get('items', [])) for qa in data['items'])
                retriever_name = data.get('meta', {}).get('retriever_name', 'Not specified')

                experiments.append({
                    'name': filename.replace('.json', ''),
                    'date': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
                    'models': list(set(answer['llm_answer']['name'] 
                             for qa in data['items'] 
                             for answer in qa['answers']['items'])),
                    'questions': len(data['items']),
                    'facts': sum(len(qa['facts']['items']) 
                              for qa in data['items'] if 'facts' in qa),
                    'chunks': total_chunks,
                    'retriever': retriever_name,
                    'results_path': file_path,
                    'validation_set': data.get('meta', {}).get('validation_set', 'Unknown')
                })

            return experiments

        except Exception as e:
            logging.error(f"Error getting experiments: {str(e)}")
            abort(500, message=str(e))

@experiment_bp.route('/experiment/<path:name>')
class ExperimentItem(MethodView):
    @experiment_bp.response(200, ExperimentSchema)
    def get(self, name):
        """Get experiment details
        
        Returns complete data for a specific experiment.
        """
        try:
            file_path = os.path.join(EVALS_FOLDER, f"{name}.json")
            if not os.path.exists(file_path):
                abort(404, message="Experiment not found")

            with open(file_path, 'r') as f:
                data = json.load(f)
            
            return data

        except Exception as e:
            logging.error(f"Error loading experiment: {str(e)}")
            abort(500, message=str(e))

    @experiment_bp.response(200, MessageResponseSchema)
    def delete(self, name):
        """Delete an experiment"""
        try:
            file_path = os.path.join(EVALS_FOLDER, f"{name}.json")
            if not os.path.exists(file_path):
                abort(404, message="Experiment not found")

            os.remove(file_path)
            return {"message": "Experiment deleted successfully"}

        except Exception as e:
            logging.error(f"Error deleting experiment: {str(e)}")
            abort(500, message=str(e))

@experiment_bp.route('/start-experiment')
class StartExperiment(MethodView):
    @experiment_bp.arguments(ExperimentConfigSchema)
    @experiment_bp.response(201, ExperimentResponseSchema)
    def post(self, config):
        """Start a new experiment
        
        Starts a new experiment with the provided configuration.
        Validates inputs, runs the experiment, and saves results.
        """
        try:
            experiment_name = config['name']

            # Check for duplicate experiment name
            if os.path.exists(os.path.join(EVALS_FOLDER, f"{experiment_name}.json")):
                abort(400, message="An experiment with this name already exists")

            # Initialize experiment
            expe = Expe()
            expe.meta['validation_set'] = config['validationSet']
            expe.meta['retriever_name'] = config.get('retrieverType', 'Not used')

            # Set up validation set data
            validation_data = config.get('validationSetData', {}).get('items', [])
            
            # Process validation set items
            for item in validation_data:
                qa = QA(
                    question=Question(text=item['question']['text']),
                    facts=Facts(items=[
                        Fact(text=f.get('text', '')) 
                        for f in item.get('facts', {}).get('items', [])
                    ])
                )
                
                # Process answers if they exist
                if item.get('answers', {}).get('items'):
                    qa.answers = Answers()
                    for answer in item['answers']['items']:
                        qa.answers.items.append(self._create_answer(answer))
                
                expe.append(qa)

            # Generate answers if needed
            if not config.get('withCSV', False):
                expe = self._generate_answers(expe, config)

            # Evaluate if requested
            if config.get('evaluateAnswers'):
                expe = self._evaluate_answers(expe, config['evaluationModel'])
            
            if config.get('evaluateChunks'):
                expe = self._evaluate_chunks(expe, config['evaluationModel'])

            # Save results
            output_path = os.path.join(EVALS_FOLDER, f"{experiment_name}.json")
            os.makedirs(EVALS_FOLDER, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(expe.model_dump(exclude_none=True), f, 
                         ensure_ascii=False, indent=2, cls=DateTimeEncoder)

            return {"message": "Experiment completed successfully", 
                    "results_path": output_path}, 201

        except Exception as e:
            logging.error(f"Error in experiment: {str(e)}")
            abort(500, message=str(e))

    def _create_answer(self, answer_data):
        """Helper to create answer object from data"""
        llm_data = answer_data.get('llm_answer', {})
        return Answer(
            text=answer_data.get('text', ''),
            llm_answer=LLMAnswer(
                meta=llm_data.get('meta', {}),
                text=llm_data.get('text', ''),
                prompt=Prompt(**llm_data.get('prompt', {})),
                name=llm_data.get('name', ''),
                timestamp=llm_data.get('timestamp', ''),
                duration=llm_data.get('duration', 0)
            )
        )

    def _generate_answers(self, expe, config):
        """Generate answers for experiment"""
        service = AnswerGeneratorService.get_instance()
        models = config['answerGenerationModels']
        use_retriever = config.get('useRetriever', False)
        retriever_type = config.get('retrieverType')
        
        if 'Albert_LLM' in models:
            prompter = AnsPrompterBase()
            use_retriever = True
            expe.meta['retriever_name'] = 'Albert_LLM (built-in retriever)'
        elif use_retriever:
            prompter = AnsPrompterWithRetrieverFR()
        else:
            prompter = AnsPrompterBase()
            expe.meta['retriever_name'] = 'No retriever'
        
        service.set_model(models, use_retriever=use_retriever, 
                         retriever_type=retriever_type)
        return service.generate_answers(expe)

    def _evaluate_answers(self, expe, model):
        """Evaluate answers for experiment"""
        service = EvaluationService.get_instance()
        service.set_model(model)
        return service.evaluate_answers(expe)

    def _evaluate_chunks(self, expe, model):
        """Evaluate chunks for experiment"""
        service = EvaluationService.get_instance()
        service.set_model(model)
        return service.evaluate_chunks(expe)
    
@experiment_bp.route('/available-models')
class AvailableModels(MethodView):
    @experiment_bp.response(200, LLMInfoSchema(many=True))
    def get(self):
        """Get available LLM models
        
        Returns a list of available LLM models with their capabilities.
        Includes both standard and custom models.
        """
        try:
            llm_info = get_llm_info()
            return llm_info

        except Exception as e:
            logging.error(f"Error getting available models: {str(e)}")
            abort(500, message=str(e))

@experiment_bp.route('/available-retrievers')
class AvailableRetrievers(MethodView):
    @experiment_bp.response(200, RetrieverInfoSchema(many=True))
    def get(self):
        """Get available retrievers
        
        Returns a list of available retriever classes that can be used
        for document retrieval in experiments.
        """
        try:
            retriever_classes = get_retriever_classes()
            retrievers = []

            for cls in retriever_classes:
                retrievers.append({
                    'name': cls.__name__,
                    'description': cls.__doc__ or 'No description available',
                    'parameters': self._get_init_parameters(cls)
                })

            return retrievers

        except Exception as e:
            logging.error(f"Error getting available retrievers: {str(e)}")
            abort(500, message=str(e))

    def _get_init_parameters(self, cls):
        """Extract initialization parameters from class"""
        import inspect
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