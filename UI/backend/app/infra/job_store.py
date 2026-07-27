"""File-based store for experiment jobs.

Gunicorn runs several worker PROCESSES: a status poll can land on a
different worker than the one executing the job, so job state cannot live
in memory. Each job is a small JSON file (status) plus a .log file (live
log lines), written by the executing worker and readable by any worker.
Status writes are atomic (tmp file + os.replace).
"""
import json
import os
import time
import re
import uuid
from datetime import datetime

from app.infra.storage import FILES_FOLDER

JOBS_FOLDER = FILES_FOLDER / 'temp' / 'jobs'

_JOB_ID_RE = re.compile(r'^[0-9a-f]{32}$')


def _validate_id(job_id):
    if not isinstance(job_id, str) or not _JOB_ID_RE.match(job_id):
        raise ValueError('Invalid job id')
    return job_id


def _job_path(job_id):
    return JOBS_FOLDER / f'{_validate_id(job_id)}.json'


def _log_path(job_id):
    return JOBS_FOLDER / f'{_validate_id(job_id)}.log'


def create_job(name):
    prune_old_jobs()
    os.makedirs(JOBS_FOLDER, exist_ok=True)
    job = {
        'id': uuid.uuid4().hex,
        'name': name,
        'status': 'queued',   # queued | running | done | failed
        'error': None,
        'results_name': None,
        'results_path': None,
        'created_at': datetime.now().isoformat(),
        'started_at': None,
        'finished_at': None,
    }
    _write(job)
    _log_path(job['id']).touch()
    return job


def _write(job):
    path = _job_path(job['id'])
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(job, f, ensure_ascii=False)
    os.replace(tmp, path)


def update_job(job_id, **fields):
    job = read_job(job_id)
    if job is None:
        return None
    job.update(fields)
    _write(job)
    return job


def read_job(job_id):
    try:
        with open(_job_path(job_id), 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def append_log(job_id, line):
    with open(_log_path(job_id), 'a', encoding='utf-8') as f:
        f.write(line.rstrip('\n') + '\n')


def read_logs(job_id, offset=0):
    """Return (lines, next_offset) with lines starting at line-index `offset`."""
    try:
        with open(_log_path(job_id), 'r', encoding='utf-8') as f:
            lines = [l.rstrip('\n') for l in f.readlines()]
    except FileNotFoundError:
        return [], offset
    offset = max(0, int(offset))
    return lines[offset:], len(lines)

# --- retention ---------------------------------------------------------
# Job status/log files accumulate forever otherwise (one pair per launched
# experiment, and the .log grows with every package log line). Old finished
# jobs are pruned when a new job is created; the frontend only polls a job
# while it is running or just after, so a few days is plenty.
JOB_RETENTION_DAYS = 7


def prune_old_jobs(max_age_days: int = JOB_RETENTION_DAYS):
    """Delete job status/log files older than `max_age_days`. Never raises."""
    try:
        if not JOBS_FOLDER.exists():
            return 0
        cutoff = time.time() - max_age_days * 86400
        removed = 0
        for path in JOBS_FOLDER.iterdir():
            if path.suffix not in ('.json', '.log', '.tmp'):
                continue
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink()
                    removed += 1
            except OSError:
                pass
        return removed
    except Exception:
        return 0
