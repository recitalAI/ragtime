import glob
import json
import logging
import os
from pathlib import Path

from flask import Blueprint, jsonify, request

from app.domain.listing import list_validation_sets
from app.infra.storage import VALIDATION_SETS_FOLDER, safe_path

validation_sets_bp = Blueprint('validation_sets', __name__, url_prefix='/api')


@validation_sets_bp.route('/validation-sets', methods=['GET'])
def get_validation_sets():
    try:
        return jsonify(list_validation_sets()), 200
    except Exception as e:
        logging.error(f"Error in get_validation_sets: {str(e)}")
        return jsonify({'error': str(e)}), 500


@validation_sets_bp.route('/validation-set/<path:name>', methods=['GET'])
def get_validation_set(name):
    try:
        try:
            file_path = safe_path(VALIDATION_SETS_FOLDER, name)
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400
        if not file_path.exists():
            return jsonify({'error': f'Validation set "{name}" not found'}), 404
        with open(file_path, 'r') as f:
            data = json.load(f)

        return jsonify(data), 200
    except Exception as e:
        logging.error(f"Error loading validation set: {str(e)}")
        return jsonify({'error': str(e)}), 500


@validation_sets_bp.route('/save-json', methods=['POST'])
def save_json():
    try:
        logging.info("Received save-json request")
        data = request.json.get('data')
        filename = request.json.get('filename')

        if not data or not filename:
            logging.error("Missing data or filename in request")
            return jsonify({'error': 'Missing data or filename'}), 400

        if not os.path.exists(VALIDATION_SETS_FOLDER):
            logging.info(f"Creating directory: {VALIDATION_SETS_FOLDER}")
            os.makedirs(VALIDATION_SETS_FOLDER)

        try:
            file_path = safe_path(VALIDATION_SETS_FOLDER, filename)
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400
        logging.info(f"Saving file to: {file_path}")

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Verify the file was saved
        if os.path.exists(file_path):
            logging.info(f"File saved successfully at {file_path}")
            return jsonify({'message': 'File saved successfully', 'path': str(file_path)}), 200
        else:
            logging.error(f"File was not saved at {file_path}")
            return jsonify({'error': 'File was not saved'}), 500
    except Exception as e:
        logging.error(f"Error saving JSON file: {str(e)}")
        return jsonify({'error': str(e)}), 500


@validation_sets_bp.route('/update-json', methods=['PUT'])
def update_json():
    try:
        data = request.json.get('data')
        new_filename = request.json.get('newFilename')
        old_filename = request.json.get('oldFilename')

        if not data or not new_filename or not old_filename:
            return jsonify({'error': 'Missing data, new filename, or old filename'}), 400

        try:
            new_file_path = safe_path(VALIDATION_SETS_FOLDER, new_filename)
            exact_old_path = safe_path(VALIDATION_SETS_FOLDER, old_filename)
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400

        # Remove the previous version: the frontend sends the exact filename;
        # the prefix glob is kept as a fallback for older clients that sent
        # only the base name.
        if exact_old_path.exists() and exact_old_path != new_file_path:
            os.remove(exact_old_path)
        else:
            legacy_pattern = os.path.join(VALIDATION_SETS_FOLDER, f"{old_filename}_Validation_set_Q*_F*.json")
            matching_files = glob.glob(legacy_pattern)
            if matching_files and Path(matching_files[0]).resolve() != new_file_path:
                os.remove(matching_files[0])

        with open(new_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        if os.path.exists(new_file_path):
            return jsonify({'message': 'File updated successfully', 'path': str(new_file_path)}), 200
        else:
            return jsonify({'error': 'File was not updated'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_sets_bp.route('/delete-validation-set/<path:name>', methods=['DELETE'])
def delete_validation_set(name):
    try:
        try:
            file_path = safe_path(VALIDATION_SETS_FOLDER, name)
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'message': 'Validation set deleted successfully'}), 200
        else:
            return jsonify({'error': 'Validation set not found'}), 404
    except Exception as e:
        logging.error(f"Error deleting validation set: {str(e)}")
        return jsonify({'error': str(e)}), 500
