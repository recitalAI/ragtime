"""Feedback API — I1.

GET    /api/feedback?name=<experiment>   -> stored feedback for that experiment
POST   /api/feedback                     -> upsert one fact's feedback entry
DELETE /api/feedback                     -> clear a fact's feedback (or one part)

The results screen loads feedback with GET (alongside the experiment JSON) to
re-display the human's votes/corrections, and writes with POST/DELETE as the
user votes.
"""
from flask import Blueprint, jsonify, request

from app.services import feedback_service

feedback_bp = Blueprint('feedback', __name__, url_prefix='/api')


@feedback_bp.route('/feedback', methods=['GET'])
def get_feedback():
    name = request.args.get('name', '', type=str)
    if not name:
        return jsonify({'error': 'Missing experiment name'}), 400
    try:
        return jsonify(feedback_service.load_feedback(name)), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@feedback_bp.route('/feedback', methods=['POST'])
def post_feedback():
    body = request.get_json(silent=True) or {}
    name = body.get('experiment') or body.get('name')
    entry = body.get('entry')
    if not name or not isinstance(entry, dict):
        return jsonify({'error': 'Body must include experiment name and an entry object'}), 400
    try:
        data = feedback_service.save_feedback_entry(name, entry)
        return jsonify(data), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@feedback_bp.route('/feedback', methods=['DELETE'])
def delete_feedback():
    body = request.get_json(silent=True) or {}
    name = body.get('experiment') or body.get('name')
    qi = body.get('question_index')
    fi = body.get('fact_index')
    which = body.get('which')  # 'passage' | 'judgment' | None (whole entry)
    if not name or qi is None or fi is None:
        return jsonify({'error': 'Body must include experiment name, question_index, fact_index'}), 400
    try:
        data = feedback_service.delete_feedback_entry(name, qi, fi, which)
        return jsonify(data), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
