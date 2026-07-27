import json
import logging
import os
from datetime import datetime

from flask import Blueprint, jsonify, request

# Importing the custom classes module registers user-defined LLM/retriever
# subclasses (docker-mounted at app/services/classes.py) so that
# class_detector can discover them and start-experiment can use them.
try:
    import app.services.classes  # noqa: F401  (user extension point; optional mount)
except ImportError:
    pass  # no user classes.py mounted — fine

from app.domain.listing import list_experiments
from app.infra.log_capture import log_capture
from app.infra.storage import EVALS_FOLDER, safe_path
from app.services.experiment_runner import run_experiment, validate_config

experiments_bp = Blueprint('experiments', __name__, url_prefix='/api')


@experiments_bp.route('/experiments', methods=['GET'])
def get_all_experiments():
    return jsonify(list_experiments()), 200


@experiments_bp.route('/start-experiment', methods=['POST'])
def start_experiment():
    """Legacy synchronous execution (kept until all clients use /api/jobs):
    runs the experiment inside the HTTP request via the same shared runner
    as the job endpoint."""
    try:
        log_capture.start_time = datetime.now()
        config = request.json
        logging.info(f"Received experiment configuration: {json.dumps(config, indent=2)}")

        error = validate_config(config)
        if error:
            return jsonify({'error': error}), 400

        try:
            output_path = run_experiment(config)
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400

        return jsonify({
            'message': 'Experiment completed successfully',
            'results_path': str(output_path),
            'results_name': os.path.basename(str(output_path)),
        })

    except Exception as e:
        logging.error(f"Unexpected error in start_experiment: {str(e)}")
        logging.exception("Traceback:")
        return jsonify({'error': f'An unexpected error occurred during the experiment: {str(e)}'}), 500


@experiments_bp.route('/experiment-results', methods=['GET'])
def get_experiment_results():
    # Preferred: fetch by result filename. The legacy `path` parameter is
    # still accepted but is reduced to its basename and resolved inside the
    # results folder — arbitrary filesystem paths are no longer readable.
    name = request.args.get('name')
    legacy_path = request.args.get('path')
    if not name and legacy_path:
        name = os.path.basename(legacy_path)
    if not name:
        return jsonify({'error': 'No results name provided'}), 400
    # Some clients still send a full path in `name` (the Home table passes
    # resultsPath) — reduce it to the filename; result filenames never
    # contain '/', so this keeps S1 (path traversal) closed.
    name = os.path.basename(name)
    if not name.endswith('.json'):
        name += '.json'

    try:
        file_path = safe_path(EVALS_FOLDER, name)
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return jsonify(data), 200
    except FileNotFoundError:
        return jsonify({'error': 'Results file not found'}), 404
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON in results file'}), 500
    except Exception as e:
        logging.error(f"Unexpected error while fetching experiment results: {str(e)}")
        return jsonify({'error': str(e)}), 500


@experiments_bp.route('/delete-experiment/<path:name>', methods=['DELETE'])
def delete_experiment(name):
    try:
        try:
            file_path = safe_path(EVALS_FOLDER, f"{name}.json")
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'message': 'Experiment deleted successfully'}), 200
        return jsonify({'error': 'Experiment not found'}), 404
    except Exception as e:
        logging.error(f"Error deleting experiment: {str(e)}")
        return jsonify({'error': str(e)}), 500
