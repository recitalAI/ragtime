from flask import Blueprint, current_app, jsonify, request

from app.infra import job_store
from app.services.experiment_runner import submit_job, validate_config

jobs_bp = Blueprint('jobs', __name__, url_prefix='/api')


@jobs_bp.route('/jobs', methods=['POST'])
def create_experiment_job():
    """Start an experiment as a background job. Returns immediately with a
    job id; progress and result are polled from GET /api/jobs/<id>. This
    replaces holding the HTTP request open for the whole experiment (which
    monopolized a gunicorn worker for up to an hour)."""
    config = request.get_json(silent=True)
    error = validate_config(config)
    if error:
        return jsonify({'error': error}), 400
    job = submit_job(current_app._get_current_object(), config)
    return jsonify({'job_id': job['id'], 'status': job['status']}), 202


@jobs_bp.route('/jobs/<job_id>', methods=['GET'])
def get_experiment_job(job_id):
    """Job status + log lines from `offset` onward (pass next_offset back
    on the following poll to receive only new lines)."""
    try:
        job = job_store.read_job(job_id)
    except ValueError:
        return jsonify({'error': 'Invalid job id'}), 400
    if job is None:
        return jsonify({'error': 'Job not found'}), 404

    offset = request.args.get('offset', 0, type=int)
    logs, next_offset = job_store.read_logs(job_id, offset)
    return jsonify({**job, 'logs': logs, 'next_offset': next_offset}), 200
