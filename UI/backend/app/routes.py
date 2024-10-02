from flask import Blueprint, request, jsonify, current_app
from app.services.answer_generator import AnswerGeneratorService
from app.services.fact_generator import FactGeneratorService
from app.services.evaluation_service import EvaluationService
from app.utils.class_detector import get_retriever_classes, get_llm_info
from app.models import db, APIKey
from ragtime.prompters import AnsPrompterBase, AnsPrompterWithRetrieverFR
from .services.classes import *
import logging
from ragtime.expe import Expe, QA, Question, Answer, Answers, Facts, Fact, Chunks, Chunk, LLMAnswer, Prompt
import json
import os 

from config import Config
from dotenv import load_dotenv, set_key, unset_key, find_dotenv
from datetime import datetime, timezone
import glob
from app.log_capture import log_capture

main = Blueprint('main', __name__)

# Get the absolute path of the current file (routes.py)
current_file_path = os.path.abspath(__file__)

# Get the directory of the current file
current_dir = os.path.dirname(current_file_path)

# Construct the path to the saved_files folder
SAVE_FOLDER = os.path.join(current_dir, '..', 'saved_files')
FOLDER_EVALS = os.path.join(current_dir, '..', 'evaluation_results')

main = Blueprint('main', __name__)

@main.route('/api/live-logs', methods=['GET'])
def get_live_logs():
    last_timestamp = request.args.get('lastTimestamp')
    if last_timestamp:
        last_timestamp = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
    
    logs, new_last_timestamp = log_capture.get_logs(last_timestamp)
    
    return jsonify({
        'logs': logs,
        'lastTimestamp': new_last_timestamp,
        'isComplete': log_capture.is_experiment_complete()
    })

@main.route('/api/user/save-env', methods=['POST'])
def save_to_env_file():
    try:
        key = request.json.get('key')
        value = request.json.get('value')
        if not key or value is None:
            return jsonify({'error': 'Key and value must be provided'}), 400

        env_path = os.path.join(current_app.root_path, '..', '.env')
        
        # Ensure the .env file exists
        if not os.path.exists(env_path):
            open(env_path, 'a').close()

        # Update or add the key-value pair
        set_key(env_path, key, value)

        # Reload the environment variables
        load_dotenv(env_path, override=True)

        return jsonify({'message': f'Environment variable {key} saved successfully'}), 200
    except Exception as e:
        current_app.logger.error(f"Error saving to .env file: {str(e)}")
        return jsonify({'error': str(e)}), 500


@main.route('/api/user/api-keys/refresh', methods=['POST'])
def refresh_api_keys():
    Config = current_app.config.get('Config')
    if Config:
        Config.update_config_with_user_keys()
    
    openai_key = Config.get_openai_api_key()
    mistral_key = Config.get_mistral_api_key()
    
    return jsonify({
        'openai': bool(openai_key),
        'mistral': bool(mistral_key)
    }), 200
    
@main.route('/api/user/api-keys', methods=['GET'])
def get_api_keys():
    keys = APIKey.query.all()
    return jsonify([{"name": key.name, "value": key.value} for key in keys]), 200

@main.route('/api/user/api-keys/availability', methods=['GET'])
def get_api_key_availability():
    openai_key = Config.get_openai_api_key()
    mistral_key = Config.get_mistral_api_key()
    
    return jsonify({
        'openai': bool(openai_key),
        'mistral': bool(mistral_key)
    }), 200

@main.route('/api/user/api-keys', methods=['POST'])
def save_api_keys():
    data = request.json
    new_keys = data.get('apiKeys', [])
    deleted_keys = data.get('deletedKeys', [])

    # Remove existing keys from database
    APIKey.query.filter_by(user_id='default').delete()

    # Add new keys to database
    for key in new_keys:
        new_key = APIKey(name=key['name'], value=key['value'], user_id='default')
        db.session.add(new_key)

    db.session.commit()

    # Update .env file and environment variables
    env_path = os.path.join(current_app.root_path, '..', '.env')
    dotenv_file = find_dotenv(env_path)

    for key_name in deleted_keys:
        unset_key(dotenv_file, key_name)
        if key_name in os.environ:
            del os.environ[key_name]

    for key in new_keys:
        set_key(dotenv_file, key['name'], key['value'])
        os.environ[key['name']] = key['value']

    # Reload the environment variables
    load_dotenv(dotenv_file, override=True)

    # Update Config object
    Config = current_app.config.get('Config')
    if Config:
        Config.update_config_with_user_keys()
    else:
        current_app.logger.error("Config class not found in app.config")

    return jsonify({"message": "API keys saved and deleted successfully"}), 200

@main.route('/api/user/api-keys/default/<key_name>', methods=['GET'])
def get_default_api_key(key_name):
    default_value = os.getenv(key_name, '')
    return jsonify({"value": default_value}), 200

@main.route('/api/save-json', methods=['POST'])
def save_json():
    try:
        logging.info("Received save-json request")
        data = request.json.get('data')
        filename = request.json.get('filename')

        logging.info(f"Filename: {filename}")
        logging.info(f"Save folder: {SAVE_FOLDER}")

        if not data or not filename:
            logging.error("Missing data or filename in request")
            return jsonify({'error': 'Missing data or filename'}), 400

        if not os.path.exists(SAVE_FOLDER):
            logging.info(f"Creating directory: {SAVE_FOLDER}")
            os.makedirs(SAVE_FOLDER)

        file_path = os.path.join(SAVE_FOLDER, filename)
        logging.info(f"Saving file to: {file_path}")

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Verify the file was saved
        if os.path.exists(file_path):
            logging.info(f"File saved successfully at {file_path}")
            return jsonify({'message': 'File saved successfully', 'path': file_path}), 200
        else:
            logging.error(f"File was not saved at {file_path}")
            return jsonify({'error': 'File was not saved'}), 500
    except Exception as e:
        logging.error(f"Error saving JSON file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/available-models', methods=['GET'])
def get_available_models():
    llm_info = get_llm_info()
    return jsonify(llm_info)

@main.route('/api/available-retrievers', methods=['GET'])
def get_available_retrievers():
    retriever_classes = get_retriever_classes()
    return jsonify([cls.__name__ for cls in retriever_classes])

@main.route('/api/validation-sets', methods=['GET'])
def get_validation_sets():
    logging.info("Fetching validation sets")
    try:
        validation_sets = []
        if not os.path.exists(SAVE_FOLDER):
            logging.warning(f"Save folder does not exist: {SAVE_FOLDER}")
            return jsonify([]), 200

        for filename in os.listdir(SAVE_FOLDER):
            if filename.endswith('.json'):
                file_path = os.path.join(SAVE_FOLDER, filename)
                logging.info(f"Processing file: {file_path}")
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)

                    # Extract name and counts from filename
                    name_parts = filename.split('_Validation_set_')
                    if len(name_parts) != 2:
                        logging.warning(f"Unexpected filename format: {filename}")
                        continue
                    name = name_parts[0]
                    counts = name_parts[1].replace('.json', '').split('_')
                    questions_count = int(counts[0][1:])
                    facts_count = int(counts[1][1:])

                    # Calculate stats
                    stats = calculate_stats(data.get('items', []))

                    file_info = {
                        'name': name,
                        'date': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
                        'questions': questions_count,
                        'facts': facts_count,
                        'chunks': stats['chunks'],
                        'answers': stats['answers'],
                        'human_eval': stats['human eval'],
                        'auto_eval': stats['auto eval'],
                        'models': stats['models']
                    }
                    validation_sets.append(file_info)
                except Exception as e:
                    logging.error(f"Error processing file {filename}: {str(e)}")

        logging.info(f"Returning {len(validation_sets)} validation sets")
        return jsonify(validation_sets), 200
    except Exception as e:
        logging.error(f"Error in get_validation_sets: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/validation-set/<path:name>', methods=['GET'])
def get_validation_set(name):
    try:
        file_path = os.path.join(SAVE_FOLDER, f"{name}_Validation_set_Q*_F*.json")
        matching_files = glob.glob(file_path)
        
        if not matching_files:
            return jsonify({'error': 'Validation set not found'}), 404
        
        if len(matching_files) > 1:
            logging.warning(f"Multiple files found for {name}, using the first one")
        
        file_path = matching_files[0]
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return jsonify(data), 200
    except Exception as e:
        logging.error(f"Error loading validation set: {str(e)}")
        return jsonify({'error': str(e)}), 500

def calculate_stats(items):
    logging.info(f"Calculating stats for {len(items)} items")
    stats = {
        "questions": len(items),
        "chunks": sum(len(qa.get('chunks', {}).get('items', [])) for qa in items),
        "facts": sum(len(qa.get('facts', {}).get('items', [])) for qa in items),
        "answers": sum(len(qa.get('answers', {}).get('items', [])) for qa in items),
        "human eval": sum(sum(1 for a in qa.get('answers', {}).get('items', []) if a.get('eval', {}).get('human')) for qa in items),
        "auto eval": sum(sum(1 for a in qa.get('answers', {}).get('items', []) if a.get('eval', {}).get('auto')) for qa in items),
        "models": len(items[0].get('answers', {}).get('items', [])) if items else 0
    }
    logging.info(f"Calculated stats: {stats}")
    return stats

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%a, %d %b %Y %H:%M:%S GMT')
        return super().default(obj)

@main.route('/api/start-experiment', methods=['POST'])
def start_experiment():
    try:
        log_capture.start_time = datetime.now() 
        config = request.json
        logging.info(f"Received experiment configuration: {json.dumps(config, indent=2)}")

        # Validate configuration
        required_fields = ['name', 'validationSet', 'evaluationModel', 'answerGenerationModels']
        if not all(field in config for field in required_fields):
            return jsonify({'error': 'Missing required fields in configuration'}), 400

        # Check for duplicate experiment name
        experiment_name = config['name']
        existing_experiments = [f.replace('.json', '') for f in os.listdir(FOLDER_EVALS) if f.endswith('.json')]
        if experiment_name in existing_experiments:
            return jsonify({'error': 'An experiment with this name already exists'}), 400

        # Initialize experiment
        expe = Expe()
        expe.meta['validation_set'] = config['validationSet']
        expe.meta['retriever_name'] = config.get('retrieverType', 'Not used')

        # Load validation set data
        if 'validationSetData' in config:
            validation_set_data = config['validationSetData']
            for item in validation_set_data['items']:
                qa = QA(
                    question=Question(text=item['question']['text']),
                    facts=Facts(items=[Fact(text=f.get('text', '')) for f in item.get('facts', {}).get('items', [])])
                )
                
                # Handle answers
                qa.answers = Answers()
                for answer_item in item.get('answers', {}).get('items', []):
                    llm_answer = answer_item.get('llm_answer', {})
                    answer = Answer(
                        text=answer_item.get('text', ''),
                        llm_answer=LLMAnswer(
                            meta=llm_answer.get('meta', {}),
                            text=llm_answer.get('text', ''),
                            prompt=Prompt(**llm_answer.get('prompt', {})),
                            name=llm_answer.get('name', ''),
                            full_name=llm_answer.get('full_name', ''),
                            timestamp=llm_answer.get('timestamp', ''),
                            duration=llm_answer.get('duration', 0),
                            chunks=llm_answer.get('chunks', [])
                        )
                    )
                    qa.answers.items.append(answer)
                
                # Handle chunks
                if 'chunks' in item and 'items' in item['chunks']:
                    qa.chunks = Chunks()
                    for chunk_item in item['chunks']['items']:
                        qa.chunks.items.append(Chunk(text=chunk_item.get('text', '')))
                
                expe.append(qa)
        else:
            # Old process: Load validation set from file
            validation_set_path = load_validation_set(config['validationSet'])
            with open(validation_set_path, 'r') as f:
                validation_set_data = json.load(f)
            for item in validation_set_data['items']:
                qa = QA(
                    question=Question(text=item['question']['text']),
                    facts=Facts(items=[Fact(text=f.get('text', '')) for f in item.get('facts', {}).get('items', [])])
                )
                expe.append(qa)

        # Generate answers if needed (old process)
        if not config['withCSV']:
            answer_generator_service = AnswerGeneratorService.get_instance()
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
            
            logging.info(f"Generating answers with models: {models}")
            answer_generator_service.set_model(models, use_retriever=use_retriever, retriever_type=retriever_type)
            expe = answer_generator_service.generate_answers(expe)

        # Evaluate answers if selected
        if config['evaluateAnswers']:
            try:
                logging.info(f"Evaluating answers with model: {config['evaluationModel']}")
                eval_generator_service = EvaluationService.get_instance()
                eval_generator_service.set_model(config['evaluationModel'])
                expe = eval_generator_service.evaluate_answers(expe)
            except Exception as e:
                logging.error(f"Error evaluating answers: {str(e)}")
                return jsonify({'error': f"Error evaluating answers: {str(e)}"}), 500

        # Evaluate chunks if selected
        if config['evaluateChunks']:
            try:
                logging.info(f"Evaluating chunks with model: {config['evaluationModel']}")
                eval_generator_service = EvaluationService.get_instance()
                eval_generator_service.set_model(config['evaluationModel'])
                expe = eval_generator_service.evaluate_chunks(expe)
            except Exception as e:
                logging.error(f"Error evaluating chunks: {str(e)}")
                return jsonify({'error': f"Error evaluating chunks: {str(e)}"}), 500

        # Save results
        output_path = os.path.join(FOLDER_EVALS, f"{experiment_name}.json")
        if not os.path.exists(FOLDER_EVALS):
            os.makedirs(FOLDER_EVALS)
        logging.info(f"Saving experiment results to: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(expe.model_dump(exclude_none=True), f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)

        logging.info(f"Experiment results saved successfully")
        return jsonify({'message': 'Experiment completed successfully', 'results_path': output_path})

    except Exception as e:
        logging.error(f"Unexpected error in start_experiment: {str(e)}")
        logging.exception("Traceback:")
        return jsonify({'error': f'An unexpected error occurred during the experiment: {str(e)}'}), 500

def load_validation_set(validation_set_prefix):
    matching_files = [f for f in os.listdir(SAVE_FOLDER) 
                      if f.startswith(validation_set_prefix) and f.endswith('.json')]
    if not matching_files:
        raise FileNotFoundError(f'No matching validation set file found for: {validation_set_prefix}')
    if len(matching_files) > 1:
        logging.warning(f"Multiple matching validation set files found for: {validation_set_prefix}. Using the first match.")
    return os.path.join(SAVE_FOLDER, matching_files[0])

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

@main.route('/api/generate-answers', methods=['POST'])
def api_generate_answers():
    try:
        logging.info("Received request for answer generation")
        data = request.json
        logging.info(f"Received data: {data}")

        expe = Expe()
        if 'items' in data:
            # Multiple questions
            for item in data['items']:
                logging.info(f"Processing item: {item}")
                qa = QA(question=Question(text=item['question']['text']))
                if 'answers' in item and 'items' in item['answers']:
                    qa.answers.items = [Answer(**a)
                                        for a in item['answers']['items']]
                expe.append(qa)
        elif 'question' in data:
            # Single question
            logging.info(f"Processing single question: {data['question']}")
            qa = QA(question=Question(text=data['question']['text']))
            expe.append(qa)
        else:
            return jsonify({'error': 'Invalid request format'}), 400

        answer_generator_service = AnswerGeneratorService.get_instance()
        
        # Use the model specified in the request
        model = data.get('model', 'gpt-4')  # Default to gpt-4 if not specified
        logging.info(f"Using model: {model}")
        use_retriever = data.get('useRetriever', False)
        retriever_type = data.get('retrieverType')
        
        answer_generator_service.set_model(models=model, use_retriever=use_retriever, retriever_type=retriever_type)

        updated_expe = answer_generator_service.generate_answers(expe)

        response = {
            'items': [
                {
                    'question': qa.question.model_dump(),
                    'answers': {
                        'items': [answer.model_dump() for answer in qa.answers.items]
                    }
                } for qa in updated_expe
            ]
        }
        logging.info("Answer generation completed successfully")
        logging.info(f"Response: {response}")
        return jsonify(response)
    except Exception as e:
        logging.error(f"Error in api_generate_answers: {str(e)}")
        logging.error(f"Error details: {type(e).__name__}, {str(e)}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/generate-facts', methods=['POST'])
def api_generate_facts():
    try:
        logging.info("Received request for fact generation")
        data = request.json
        logging.info(f"Received data: {data}")

        expe = Expe()
        if 'items' in data:
            for item in data['items']:
                logging.info(f"Processing item: {item}")
                qa = QA(question=Question(text=item['question']['text']))
                if 'answers' in item and 'items' in item['answers']:
                    qa.answers.items = []
                    for a in item['answers']['items']:
                        try:
                            if isinstance(a['llm_answer']['timestamp'], str):
                                # Try different timestamp formats
                                timestamp = None
                                for fmt in ['%Y-%m-%dT%H:%M:%S.%f', '%a, %d %b %Y %H:%M:%S GMT']:
                                    try:
                                        timestamp = datetime.strptime(a['llm_answer']['timestamp'], fmt)
                                        if fmt == '%Y-%m-%dT%H:%M:%S.%f':
                                            timestamp = timestamp.replace(tzinfo=timezone.utc)
                                        break
                                    except ValueError:
                                        continue
                                
                                if timestamp is None:
                                    raise ValueError(f"Unable to parse timestamp: {a['llm_answer']['timestamp']}")
                                
                                a['llm_answer']['timestamp'] = timestamp
                            
                            qa.answers.items.append(Answer(**a))
                        except ValueError as e:
                            logging.error(f"Error parsing answer: {e}")
                expe.append(qa)
        else:
            return jsonify({'error': 'Invalid request format'}), 400

        fact_generator_service = FactGeneratorService.get_instance()
        
        # Use the model specified in the request
        model = data.get('model', 'gpt-4')  # Default to gpt-4 if not specified
        logging.info(f"Using model: {model}")
        fact_generator_service.set_model(model)
        
        updated_expe = fact_generator_service.generate_facts(expe)

        response = {
            'items': [
                {
                    'question': qa.question.model_dump(),
                    'facts': qa.facts.model_dump() if qa.facts else None
                } for qa in updated_expe
            ]
        }
        logging.info("Fact generation completed successfully")
        logging.info(f"Response: {response}")
        return jsonify(response)
    except Exception as e:
        logging.error(f"Error in api_generate_facts: {str(e)}")
        logging.error(f"Error details: {type(e).__name__}, {str(e)}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/experiments', methods=['GET'])
def get_all_experiments():
    try:
        experiments = []
        for filename in os.listdir(FOLDER_EVALS):
            if filename.endswith('.json'):
                file_path = os.path.join(FOLDER_EVALS, filename)
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Calculate total chunks
                total_chunks = sum(len(qa.get('chunks', {}).get('items', [])) for qa in data['items'])
                
                # Get retriever name (assuming it's stored in the metadata)
                retriever_name = data.get('meta', {}).get('retriever_name', 'Not specified')
                
                experiment_info = {
                    'name': filename.replace('.json', ''),
                    'date': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
                    'models': list(set(answer['llm_answer']['name'] for qa in data['items'] for answer in qa['answers']['items'])),
                    'questions': len(data['items']),
                    'facts': sum(len(qa['facts']['items']) for qa in data['items'] if 'facts' in qa),
                    'chunks': total_chunks,
                    'retriever': retriever_name,
                    'resultsPath': file_path,
                    'validationSet': data.get('meta', {}).get('validation_set', 'Unknown')
                }
                experiments.append(experiment_info)
        
        return jsonify(experiments), 200
    except Exception as e:
        logging.error(f"Error in get_all_experiments: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/update-json', methods=['PUT'])
def update_json():
    try:
        data = request.json.get('data')
        new_filename = request.json.get('newFilename')
        old_filename = request.json.get('oldFilename')

        if not data or not new_filename or not old_filename:
            return jsonify({'error': 'Missing data, new filename, or old filename'}), 400

        old_file_path = os.path.join(SAVE_FOLDER, f"{old_filename}_Validation_set_Q*_F*.json")
        matching_files = glob.glob(old_file_path)
        
        if matching_files:
            old_file_path = matching_files[0]
            os.remove(old_file_path)

        new_file_path = os.path.join(SAVE_FOLDER, new_filename)

        with open(new_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        if os.path.exists(new_file_path):
            return jsonify({'message': 'File updated successfully', 'path': new_file_path}), 200
        else:
            return jsonify({'error': 'File was not updated'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main.route('/api/delete-validation-set/<path:name>', methods=['DELETE'])
def delete_validation_set(name):
    try:
        file_path = os.path.join(SAVE_FOLDER, name)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'message': 'Validation set deleted successfully'}), 200
        else:
            return jsonify({'error': 'Validation set not found'}), 404
    except Exception as e:
        logging.error(f"Error deleting validation set: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/delete-experiment/<path:name>', methods=['DELETE'])
def delete_experiment(name):
    try:
        file_path = os.path.join(FOLDER_EVALS, f"{name}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'message': 'Experiment deleted successfully'}), 200
        else:
            return jsonify({'error': 'Experiment not found'}), 404
    except Exception as e:
        logging.error(f"Error deleting experiment: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/experiment-results', methods=['GET'])
def get_experiment_results():
    results_path = request.args.get('path')
    if not results_path:
        logging.error("No results path provided in the request")
        return jsonify({'error': 'No results path provided'}), 400
    
    logging.info(f"Fetching experiment results from: {results_path}")
    
    try:
        with open(results_path, 'r') as f:
            data = json.load(f)
        logging.info(f"Successfully loaded experiment results from {results_path}")
        return jsonify(data), 200
    except FileNotFoundError:
        logging.error(f"Results file not found: {results_path}")
        return jsonify({'error': 'Results file not found'}), 404
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in results file: {results_path}")
        return jsonify({'error': 'Invalid JSON in results file'}), 500
    except Exception as e:
        logging.error(f"Unexpected error while fetching experiment results: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Add this at the end of the file
if __name__ == '__main__':
    main.run(debug=True)