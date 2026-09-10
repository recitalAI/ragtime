from flask import Blueprint, current_app, jsonify, request, send_file

from app.infra import job_store
from app.services.experiment_runner import (
    submit_job, submit_evaluation_job, validate_config, build_debug_excel,
)
from app.services.connectivity import check_internet, OFFLINE_STATUS, OFFLINE_ERROR

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
    # Outbound-connectivity gate: an experiment runs answer generation and/or
    # evaluation, all of which call external providers. Check before creating
    # the job so an offline container fails fast with a clear message instead
    # of spawning a job that errors on every call.
    if not check_internet():
        import logging
        logging.warning("Experiment launch blocked: no outbound internet connectivity.")
        return jsonify(OFFLINE_ERROR), OFFLINE_STATUS
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


@jobs_bp.route('/jobs/<job_id>/review', methods=['GET'])
def get_reviewed_job(job_id):
    """Return the retrieved question / answer / chunks for a job awaiting
    review, so the frontend can show the checkpoint. Read-only; the pending
    data stays until the user evaluates or discards."""
    from ragtime.expe import Expe
    from app.services import review_store

    try:
        job = job_store.read_job(job_id)
    except ValueError:
        return jsonify({'error': 'Invalid job id'}), 400
    if job is None:
        return jsonify({'error': 'Job not found'}), 404

    pending = review_store.load_pending(job_id)
    if pending is None:
        return jsonify({'error': 'No reviewed data found (it may have expired).'}), 404

    expe = Expe()
    expe.load_from_dict(pending['expe'])
    cfg = pending.get('config') or {}

    items = []
    for qa in expe:
        answer = ''
        if qa and qa.answers and qa.answers.items:
            answer = qa.answers.items[0].text or ''
        chunks = [c.text for c in qa.chunks.items] if (qa and qa.chunks and qa.chunks.items) else []
        items.append({
            'question': qa.question.text if (qa and qa.question) else '',
            'answer': answer,
            'chunks': chunks,
        })

    return jsonify({
        'job_id': job_id,
        'status': job.get('status'),
        'name': cfg.get('name'),
        'evaluateChunks': cfg.get('evaluateChunks', False),
        'items': items,
    }), 200


@jobs_bp.route('/jobs/<job_id>/evaluate', methods=['POST'])
def evaluate_reviewed_job(job_id):
    """Approve the checkpoint: launch phase-2 evaluation for a job that is
    awaiting review (Search retriever flow). Returns 202; progress is polled
    from GET /api/jobs/<id> as usual."""
    try:
        job = job_store.read_job(job_id)
    except ValueError:
        return jsonify({'error': 'Invalid job id'}), 400
    if job is None:
        return jsonify({'error': 'Job not found'}), 404
    if job.get('status') != 'awaiting_review':
        return jsonify({'error': 'Job is not awaiting review'}), 409
    # Evaluation calls external providers — same fast-fail gate as launch.
    if not check_internet():
        import logging
        logging.warning("Evaluation launch blocked: no outbound internet connectivity.")
        return jsonify(OFFLINE_ERROR), OFFLINE_STATUS
    updated = submit_evaluation_job(current_app._get_current_object(), job_id)
    return jsonify({'job_id': job_id, 'status': (updated or job)['status']}), 202


@jobs_bp.route('/jobs/<job_id>/discard', methods=['POST'])
def discard_reviewed_job(job_id):
    """Stop at the checkpoint: return a debug .xlsx (question / answer /
    chunks) for inspection, then drop the pending data and clean the session.
    No experiment is saved and no evaluation is run."""
    from ragtime.expe import Expe
    from app.services import review_store

    try:
        job = job_store.read_job(job_id)
    except ValueError:
        return jsonify({'error': 'Invalid job id'}), 400
    if job is None:
        return jsonify({'error': 'Job not found'}), 404

    pending = review_store.load_pending(job_id)
    if pending is None:
        return jsonify({'error': 'No reviewed data found (it may have expired).'}), 404

    expe = Expe()
    expe.load_from_dict(pending['expe'])
    name = (pending.get('config') or {}).get('name') or 'experiment'
    xlsx_path = build_debug_excel(expe, name)

    # Clean up: drop the pending data and mark the job discarded.
    review_store.discard_pending(job_id)
    job_store.update_job(job_id, status='discarded')

    return send_file(
        str(xlsx_path),
        as_attachment=True,
        download_name=f'{name}_search_debug.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
