"""Human feedback storage — I1.

Each experiment gets one JSON file under files/feedback/<experiment>.json that
records the human's qualitative feedback on the LLM evaluation, per fact:
  - passage feedback  (was the extracted "generated text" right?), and/or
  - judgment feedback (was the eval's comment/verdict reasoning right?).

The goal is to measure passage-extraction quality and judgment quality
separately, to later improve the evaluation prompts. Feedback lives in its own
folder (not in the experiment JSON, which is regenerated each run) and is read
back alongside the experiment on the results screen for consistency.

A feedback entry is keyed by (question_index, fact_index) — the stable position
in the experiment JSON — and also stores question_text / fact_text for
readability and robustness when the feedback is analysed later.
"""
import json
import os
from datetime import datetime

from app.infra.storage import FEEDBACK_FOLDER, safe_path


def _feedback_path(experiment_name):
    """Resolve files/feedback/<name>.json safely. `experiment_name` is the
    results file name; we store feedback under the same stem + .json."""
    stem = experiment_name[:-5] if experiment_name.endswith('.json') else experiment_name
    return safe_path(FEEDBACK_FOLDER, f'{stem}.json')


def load_feedback(experiment_name):
    """Return the stored feedback dict for an experiment, or an empty skeleton
    if none exists yet."""
    try:
        path = _feedback_path(experiment_name)
    except ValueError:
        return {'experiment': experiment_name, 'items': []}
    if not path.exists():
        return {'experiment': experiment_name, 'items': []}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict) or 'items' not in data:
            return {'experiment': experiment_name, 'items': []}
        return data
    except (json.JSONDecodeError, OSError):
        return {'experiment': experiment_name, 'items': []}


def _entry_key(entry):
    return (entry.get('question_index'), entry.get('fact_index'))


def save_feedback_entry(experiment_name, entry):
    """Upsert one fact's feedback entry (keyed by question_index+fact_index).
    Merges passage/judgment so a later judgment vote doesn't wipe an earlier
    passage vote. Returns the full updated feedback dict."""
    if not isinstance(entry, dict):
        raise ValueError('Feedback entry must be an object')
    if entry.get('question_index') is None or entry.get('fact_index') is None:
        raise ValueError('Feedback entry needs question_index and fact_index')

    data = load_feedback(experiment_name)
    items = data.setdefault('items', [])
    key = _entry_key(entry)
    entry['timestamp'] = datetime.now().isoformat(timespec='seconds')

    existing = next((it for it in items if _entry_key(it) == key), None)
    if existing is None:
        items.append(entry)
    else:
        # Merge: refresh the scalar fields, and overwrite whichever facet(s) the
        # request provided. Looping over the known facets (instead of listing
        # them one by one) means every facet — verdict, passage, judgment — can
        # be modified in any direction (up<->down, changed correction), and no
        # facet is ever forgotten.
        for k in ('question_text', 'fact_text', 'status', 'timestamp'):
            if k in entry:
                existing[k] = entry[k]
        for facet in ('verdict', 'passage', 'judgment'):
            if facet in entry:
                existing[facet] = entry[facet]

    os.makedirs(FEEDBACK_FOLDER, exist_ok=True)
    path = _feedback_path(experiment_name)
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return data


def delete_feedback_entry(experiment_name, question_index, fact_index, which=None):
    """Remove a fact's feedback, or just its 'passage'/'judgment' part when
    `which` is given (used when the user clears a single vote). Returns the
    updated feedback dict."""
    data = load_feedback(experiment_name)
    items = data.get('items', [])
    key = (question_index, fact_index)
    existing = next((it for it in items if _entry_key(it) == key), None)
    if existing is None:
        return data
    if which in ('passage', 'judgment', 'verdict'):
        existing.pop(which, None)
        # If no facet remains, drop the whole entry.
        if not any(k in existing for k in ('passage', 'judgment', 'verdict')):
            data['items'] = [it for it in items if _entry_key(it) != key]
    else:
        data['items'] = [it for it in items if _entry_key(it) != key]

    os.makedirs(FEEDBACK_FOLDER, exist_ok=True)
    path = _feedback_path(experiment_name)
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return data
