# UI\backend\app\apis\validation_routes.py
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import request, jsonify
from .models.validation_models import *
import os
import json
import glob
from app.routes import SAVE_FOLDER, calculate_stats
import logging
from datetime import datetime

validation_bp = Blueprint('validation_api', 'Validation operations', url_prefix='/api')

@validation_bp.route('/validation-sets')
class ValidationSets(MethodView):
    @validation_bp.response(200, ValidationSetStatsSchema(many=True))
    def get(self):
        """Get all validation sets with their statistics"""
        try:
            validation_sets = []
            if not os.path.exists(SAVE_FOLDER):
                return []

            for filename in os.listdir(SAVE_FOLDER):
                if not filename.endswith('.json'):
                    continue
                    
                file_path = os.path.join(SAVE_FOLDER, filename)
                with open(file_path, 'r') as f:
                    data = json.load(f)

                name_parts = filename.split('_Validation_set_')
                if len(name_parts) != 2:
                    continue
                    
                name = name_parts[0]
                counts = name_parts[1].replace('.json', '').split('_')
                questions_count = int(counts[0][1:])
                facts_count = int(counts[1][1:])

                stats = calculate_stats(data.get('items', []))
                validation_sets.append({
                    'name': name,
                    'date': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
                    'questions': questions_count,
                    'facts': facts_count,
                    'chunks': stats['chunks'],
                    'answers': stats['answers'],
                    'human_eval': stats['human eval'],
                    'auto_eval': stats['auto eval'],
                    'models': stats['models']
                })

            return validation_sets

        except Exception as e:
            logging.error(f"Error getting validation sets: {str(e)}")
            abort(500, message=str(e))

    @validation_bp.arguments(ValidationSetSchema)
    @validation_bp.response(200, ValidationSetSchema) 
    def post(self, data):
        """Upload and validate a validation set"""
        try:
            name = data.get('name')
            if not name:
                abort(400, message="Validation set must have a name")

            items = data.get('items', [])
            if not items:
                abort(400, message="Validation set must contain items")

            for item in items:
                if not item.get('question', {}).get('text'):
                    abort(400, message="Each item must have question.text")
                if not item.get('facts', {}).get('items'):
                    abort(400, message="Each item must have facts.items")

            questions_count = len(items)
            facts_count = sum(len(item.get('facts', {}).get('items', [])) for item in items)
            filename = f"{name}_Validation_set_Q{questions_count}_F{facts_count}.json"

            if not os.path.exists(SAVE_FOLDER):
                os.makedirs(SAVE_FOLDER)

            file_path = os.path.join(SAVE_FOLDER, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return data

        except Exception as e:
            logging.error(f"Error saving validation set: {str(e)}")
            abort(500, message=str(e))

@validation_bp.route('/validation-set/<path:name>')
class ValidationSet(MethodView):
    @validation_bp.response(200, MessageResponseSchema)
    def delete(self, name):
        """Delete a validation set"""
        try:
            search_pattern = os.path.join(SAVE_FOLDER, f"{name}_Validation_set_Q*_F*.json")
            matching_files = glob.glob(search_pattern)
            
            if not matching_files:
                abort(404, message="Validation set not found")

            for filepath in matching_files:
                try:
                    os.remove(filepath)
                except OSError as e:
                    logging.error(f"Error deleting file {filepath}: {str(e)}")
                    abort(500, message=f"Failed to delete file {filepath}")

            return {"message": f"Successfully deleted validation set '{name}'"}
            
        except Exception as e:
            logging.error(f"Error deleting validation set: {str(e)}")
            abort(500, message=str(e))

@validation_bp.route('/validation-set-content/<path:name>')
class ValidationSetContent(MethodView):
    @validation_bp.response(200, ValidationSetSchema)
    def get(self, name):
        """Get complete content of a validation set
        
        Returns the full JSON content of the specified validation set.
        ---
        Parameters:
            - name (str): Name of the validation set
        Returns:
            Full validation set JSON content
        """
        try:
            pattern = os.path.join(SAVE_FOLDER, f"{name}_Validation_set_Q*_F*.json")
            matching_files = glob.glob(pattern)
            
            if not matching_files:
                abort(404, message="Validation set not found")
            
            with open(matching_files[0], 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return jsonify(data)
        except Exception as e:
            logging.error(f"Error loading validation set content: {str(e)}")
            abort(500, message=str(e))