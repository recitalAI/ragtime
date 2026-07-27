"""Folder listings for the Home page, with an mtime-keyed cache (B6 fix).

Parsing a results/validation JSON into a pydantic `Expe` is the expensive
part of the Home page. Each file is re-parsed only when its mtime changed
since the last listing; unchanged files are served from the per-process
cache. Entries removed from disk are evicted. The response shapes are
exactly the ones the frontend tables consume (unchanged from the former
routes.py handlers).
"""
import logging
import os
from datetime import datetime

from ragtime.expe import Expe

from app.infra.storage import EVALS_FOLDER, VALIDATION_SETS_FOLDER

_experiments_cache = {}      # filename -> (mtime, entry)
_validation_sets_cache = {}  # filename -> (mtime, entry)


def _list_folder(folder, cache, build_entry):
    if not os.path.exists(folder):
        logging.warning(f"Folder does not exist: {folder}")
        return []

    entries = []
    seen = set()
    for filename in os.listdir(folder):
        if not filename.endswith('.json'):
            continue
        file_path = os.path.join(folder, filename)
        try:
            mtime = os.path.getmtime(file_path)
            cached = cache.get(filename)
            if cached is not None and cached[0] == mtime:
                entry = cached[1]
            else:
                entry = build_entry(filename, file_path, mtime)
                cache[filename] = (mtime, entry)
            seen.add(filename)
            entries.append(entry)
        except Exception as e:
            logging.error(f'Cannot load "{filename}" - skip it\n{e}')

    # Evict cache entries whose files were deleted or failed to parse.
    for stale in set(cache) - seen:
        cache.pop(stale, None)

    # Sort by date, newest first (the date string format sorts correctly).
    return sorted(entries, key=lambda x: x['date'], reverse=True)


# --- Cost aggregation (Home page "Price" column) -----------------------------
# Costs are already stored per LLM call inside each result/validation JSON, on
# the `llm_answer.cost` field (in USD). Imported data has cost 0 (or no
# llm_answer), so the sums below naturally come out to 0 for it — nothing is
# recomputed here, we only add up what the pipeline already recorded.
#
# Three cost sources exist in the model (see ragtime.expe):
#   - qa.answers[].llm_answer.cost        -> answer generation
#   - qa.answers[].eval.llm_answer.cost   -> answer evaluation (incl. RAG/chunk
#                                             eval, which the pipeline attaches
#                                             to the same eval llm_answer)
#   - qa.facts.llm_answer.cost            -> fact generation (one call per QA)


def _llm_cost(obj) -> float:
    """Return obj.llm_answer.cost as a float, or 0.0 when absent/None."""
    la = getattr(obj, 'llm_answer', None) if obj is not None else None
    if la is None:
        return 0.0
    return la.cost or 0.0


def _answer_gen_cost(expe) -> float:
    return sum(_llm_cost(a) for qa in expe for a in (qa.answers or []) if a)


def _answer_eval_cost(expe) -> float:
    return sum(
        _llm_cost(a.eval)
        for qa in expe for a in (qa.answers or [])
        if a and a.eval
    )


def _fact_gen_cost(expe) -> float:
    return sum(_llm_cost(qa.facts) for qa in expe if qa and qa.facts)


def _experiment_entry(filename, file_path, mtime):
    expe: Expe = Expe(file_path)
    stats = expe.stats()
    return {
        'name': filename.replace('.json', ''),
        'date': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'models': list(set(answer.llm_answer.name for qa in expe for answer in qa.answers)),
        'questions': stats['questions'],
        'facts': stats['facts'],
        'chunks': stats['chunks'],
        'retriever': expe.meta.get('retriever_name', 'Not specified'),
        'resultsPath': file_path,
        'validationSet': expe.meta.get('validation_set', 'Unknown'),
        # Experiment total = answer generation + evaluation (answer eval, plus
        # RAG/chunk eval when it was activated — both live on the eval call).
        # Answer-gen cost is already 0 for Excel-imported answers.
        'cost': _answer_gen_cost(expe) + _answer_eval_cost(expe),
    }


def _validation_set_entry(filename, file_path, mtime):
    expe: Expe = Expe(file_path)
    stats = expe.stats()
    return {
        'name': filename,
        'date': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'questions': stats['questions'],
        'facts': stats['facts'],
        'chunks': stats['chunks'],
        'answers': stats['answers'],
        'human_eval': stats['human eval'],
        'auto_eval': stats['auto eval'],
        'models': stats['models'],
        # Validation-set total = answer generation + fact generation. Both are 0
        # when the user imported the data (no price recorded).
        'cost': _answer_gen_cost(expe) + _fact_gen_cost(expe),
    }


def list_experiments():
    return _list_folder(EVALS_FOLDER, _experiments_cache, _experiment_entry)


def list_validation_sets():
    return _list_folder(VALIDATION_SETS_FOLDER, _validation_sets_cache, _validation_set_entry)
