import logging

from flask import Blueprint, jsonify, request

from ragtime.expe import QA, Answer, Expe, Question

from app.services import key_service
from app.services.answer_generator import AnswerGeneratorService
from app.services.fact_generator import FactGeneratorService

generation_bp = Blueprint('generation', __name__, url_prefix='/api')

_EXPECTED_FORMAT = """Invalid request format. Expected JSON: {'items': [{'question': {'text': ...}, 'answers': {'items': [{'text': ...}]}}], 'model': '<model name>'}"""


@generation_bp.route('/generate-answers', methods=['POST'])
def api_generate_answers():
    try:
        logging.info("Received request for answer generation")
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'Request body must be a JSON object. ' + _EXPECTED_FORMAT}), 400
        if not data.get('model'):
            return jsonify({'error': "Missing 'model' in request. Please select an answer generation model."}), 400

        expe = Expe()
        if 'items' in data:
            if not isinstance(data['items'], list) or not data['items']:
                return jsonify({'error': "'items' must be a non-empty list of questions."}), 400
            # Multiple questions
            for i, item in enumerate(data['items']):
                try:
                    qa = QA(question=Question(text=item['question']['text']))
                    if 'answers' in item and 'items' in item['answers']:
                        qa.answers.items = [Answer(**a)
                                            for a in item['answers']['items']]
                except (KeyError, TypeError) as item_error:
                    return jsonify({'error': f'Item {i + 1} is malformed ({item_error}). ' + _EXPECTED_FORMAT}), 400
                expe.append(qa)
        elif 'question' in data:
            # Single question
            logging.info(f"Processing single question: {data['question']}")
            qa = QA(question=Question(text=data['question']['text']))
            expe.append(qa)
        else:
            return jsonify({'error': 'Invalid request format'}), 400

        model = data['model']
        use_retriever = data.get('useRetriever', False)
        retriever_type = data.get('retrieverType')
        logging.info(f"Using model: {model}")

        # Keys may have been saved through another worker process since this
        # one started — re-apply DB -> env before the LLM call.
        key_service.ensure_fresh()
        generator = AnswerGeneratorService(model, use_retriever=use_retriever, retriever_type=retriever_type)
        updated_expe = generator.generate_answers(expe)

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


@generation_bp.route('/generate-facts', methods=['POST'])
def api_generate_facts():
    try:
        logging.info("Received request for fact generation")
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'Request body must be a JSON object. ' + _EXPECTED_FORMAT}), 400
        if not data.get('model'):
            return jsonify({'error': "Missing 'model' in request. Please select a fact generation model."}), 400

        if isinstance(data.get('items'), list) and data['items']:
            try:
                expe = Expe(json_dict=data['items'])
            except Exception as parse_error:
                logging.error(f"Invalid items format for fact generation: {parse_error}")
                return jsonify({'error': f'Invalid validation set format: {parse_error}'}), 400
        else:
            return jsonify({'error': "Missing or empty 'items' list. " + _EXPECTED_FORMAT}), 400

        model = data['model']
        logging.info(f"Using model: {model}")

        key_service.ensure_fresh()
        generator = FactGeneratorService(model)
        updated_expe = generator.generate_facts(expe)

        response = {
            'items': [
                {
                    'question': qa.question.model_dump(),
                    'facts': qa.facts.model_dump() if qa.facts else None
                } for qa in updated_expe
            ]
        }
        logging.info("Fact generation completed successfully")
        return jsonify(response)
    except Exception as e:
        logging.error(f"Error in api_generate_facts: {str(e)}")
        logging.error(f"Error details: {type(e).__name__}, {str(e)}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500
