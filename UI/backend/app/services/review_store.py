"""On-disk store for an experiment awaiting human review (the checkpoint).

When a retriever runs in two phases — retrieve (answers + chunks) then, after a
human check, evaluate — the intermediate Expe must survive between the two HTTP
requests. Gunicorn runs several worker PROCESSES, so the second request (launch
evaluation / discard) can land on a different worker than the one that ran the
retrieval. In-memory state would be invisible to that worker, so we persist the
pending Expe as a JSON file keyed by job id, exactly like the file-based
job_store next to it.

Stored: the serialized Expe plus the config needed for phase 2 (evaluation
model, whether to evaluate chunks, the experiment name). The Search token is
NEVER stored here.
"""
import json
import os

from app.infra.storage import FILES_FOLDER
from app.infra.job_store import _validate_id  # reuse the same id validation

REVIEW_FOLDER = FILES_FOLDER / 'temp' / 'reviews'


def _review_path(job_id):
    return REVIEW_FOLDER / f'{_validate_id(job_id)}.json'


def save_pending(job_id, expe_json, config):
    """Persist the pending Expe (as a JSON string or dict) plus the phase-2
    config. Never store the Search token."""
    os.makedirs(REVIEW_FOLDER, exist_ok=True)
    safe_config = {
        'name': config.get('name'),
        'evaluationModel': config.get('evaluationModel'),
        'evaluateAnswers': config.get('evaluateAnswers', True),
        'evaluateChunks': config.get('evaluateChunks', False),
        'retrieverType': config.get('retrieverType'),
    }
    payload = {
        'expe': expe_json if isinstance(expe_json, (dict, list)) else json.loads(expe_json),
        'config': safe_config,
    }
    path = _review_path(job_id)
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False)
    os.replace(tmp, path)
    return path


def load_pending(job_id):
    """Return {'expe': ..., 'config': ...} or None if not found."""
    try:
        with open(_review_path(job_id), 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def has_pending(job_id):
    return _review_path(job_id).exists()


def discard_pending(job_id):
    """Delete the pending file. Never raises."""
    try:
        _review_path(job_id).unlink()
        return True
    except OSError:
        return False
