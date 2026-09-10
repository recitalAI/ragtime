"""Runs an experiment: shared by the legacy synchronous endpoint and the
job-based endpoint (Phase 3).

Also restores the Excel/CSV path: when the frontend imports answers from a
spreadsheet (withCSV), it sends the merged data in `validationSetData`.
The endpoint code that consumed it had been dead (commented out) — the
backend silently evaluated the file's gold answers instead of the imported
ones. The runner now builds the Expe from `validationSetData` in that case.
"""
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from ragtime.expe import Expe

from app.infra import job_store
from app.infra.storage import EVALS_FOLDER, VALIDATION_SETS_FOLDER, safe_path
from app.services.answer_generator import AnswerGeneratorService
from app.services.evaluation_service import EvaluationService

# One experiment at a time per worker process; polling is served by any
# worker from the file-based job store.
_executor = ThreadPoolExecutor(max_workers=1)

REQUIRED_FIELDS = ['name', 'validationSet', 'evaluationModel', 'answerGenerationModels']


def validate_config(config):
    if not isinstance(config, dict):
        return 'Configuration must be a JSON object'
    # Search supplies both answers and chunks itself, so it needs no
    # answer-generation model; the other fields are still required.
    required = list(REQUIRED_FIELDS)
    if _is_search_retriever(config):
        required = [f for f in required if f != 'answerGenerationModels']
    if not all(field in config for field in required):
        return 'Missing required fields in configuration'
    return None


def _normalize_csv_items(items):
    """QA-level `chunks` is a Chunks container ({items: [{text}]}); the Excel
    import sometimes builds it as a bare list of strings — wrap it.
    `llm_answer.chunks` is an untyped plain list in the package model and is
    left exactly as the frontend sent it."""
    for item in items:
        chunks = item.get('chunks')
        if isinstance(chunks, list):
            item['chunks'] = {'items': [c if isinstance(c, dict) else {'text': c} for c in chunks]}
    return items


def _csv_items_have_chunks(items):
    """True if any imported CSV/Excel item actually carries retrieved chunks.
    Chunks can sit at the QA level (`chunks.items`) or on the answer
    (`answers.items[].llm_answer.chunks`); we treat the item as having chunks
    if either holds a non-empty list. Used to label the experiment's retriever
    correctly: importing only answers must read as "No retriever", while
    importing answers *with* chunks reads as a custom retriever."""
    for item in items or []:
        qa_chunks = (item.get('chunks') or {})
        if isinstance(qa_chunks, dict) and qa_chunks.get('items'):
            return True
        if isinstance(qa_chunks, list) and qa_chunks:
            return True
        for ans in ((item.get('answers') or {}).get('items') or []):
            la = ans.get('llm_answer') or {}
            if la.get('chunks'):
                return True
    return False


def build_expe(config):
    validation_set_data = config.get('validationSetData')
    is_csv = bool(config.get('withCSV') and isinstance(validation_set_data, dict) and validation_set_data.get('items'))
    if is_csv:
        # Excel/CSV path: use the answers the user imported and matched.
        items = _normalize_csv_items(validation_set_data['items'])
        expe = Expe(json_dict=items)
    else:
        validation_set_path = safe_path(VALIDATION_SETS_FOLDER, config['validationSet'])
        if not validation_set_path.exists():
            raise ValueError(f'Validation set "{config["validationSet"]}" not found')
        expe = Expe(validation_set_path)

    expe.meta['validation_set'] = config['validationSet']
    if is_csv:
        # No retriever ran here - the answers (and any chunks) were imported.
        # Label by what was actually imported: chunks present => a retriever
        # produced them upstream (custom), otherwise answers only => none.
        expe.meta['retriever_name'] = 'Custom retriever' if _csv_items_have_chunks(items) else 'No retriever'
    else:
        expe.meta['retriever_name'] = config.get('retrieverType', 'Not used')
    return expe


# ── Search retriever: two-phase flow (retrieve -> review -> evaluate) ────────
# The mechanism is generic (retrieve, checkpoint, evaluate) so a future
# retriever can reuse it; only `_is_search_retriever` and the retrieval call
# are Search-specific.

def _is_search_retriever(config):
    """True when the experiment should pull answers AND chunks from Search
    instead of generating them with an LLM."""
    return (config.get('useRetriever')
            and str(config.get('retrieverType', '')).strip().lower() == 'search')


def _questions_with_facts(expe):
    """Extract [{question, facts:[{text}]}] from a loaded validation-set Expe,
    to feed Search retrieval while preserving the gold facts for evaluation."""
    out = []
    for qa in expe:
        q = qa.question.text if qa and qa.question else ''
        facts = []
        if qa and qa.facts and qa.facts.items:
            facts = [{'text': f.text} for f in qa.facts.items]
        out.append({'question': q, 'facts': facts})
    return out


def run_search_phase1(config, token, folder_id=None, log=None):
    """Phase 1: retrieve answers + chunks from Search, build the Expe, and
    return it (unsaved). Raises on failure. Does not evaluate anything."""
    from app.services import search_service

    base = build_expe(config)                       # loads validation set + meta
    base.meta['retriever_name'] = 'Search'
    questions = _questions_with_facts(base)

    expe = search_service.run_search_retrieval(questions, token, folder_id, log=log)
    # Carry the validation-set meta onto the answered Expe.
    expe.meta['validation_set'] = config.get('validationSet')
    expe.meta['retriever_name'] = 'Search'
    return expe


def run_evaluation_phase2(expe, config):
    """Phase 2: evaluate an already-retrieved Expe (answers + chunks present)
    and save it. Mirrors the evaluation part of run_experiment. Returns the
    output path."""
    if config.get('evaluateAnswers', True):
        logging.info(f"Evaluating answers with model: {config['evaluationModel']}")
        evaluator = EvaluationService(config['evaluationModel'])
        expe = evaluator.evaluate_answers(expe)

    if config.get('evaluateChunks'):
        logging.info(f"Evaluating chunks with model: {config['evaluationModel']}")
        evaluator = EvaluationService(config['evaluationModel'])
        expe = evaluator.evaluate_chunks(expe)

    # Same flags as the normal flow, for the results UI.
    expe.meta['evaluate_answers'] = bool(config.get('evaluateAnswers', True))
    expe.meta['evaluate_chunks'] = bool(config.get('evaluateChunks', False))

    # Guard against a package quirk: EvalGeneratorChunks assigns a *dict* to
    # `answer.llm_answer` (e.g. {"name": "Hallucinations Eval"}) via direct
    # assignment, which Pydantic does not coerce to an LLMAnswer. Expe.stats()
    # (called by save_to_json -> get_name) then does `llm_answer.name` and
    # crashes with "'dict' object has no attribute 'name'". Normalize any dict
    # llm_answer back into an LLMAnswer object before saving.
    _normalize_llm_answers(expe)

    return expe.save_to_json(path=EVALS_FOLDER / config['name'])


def _normalize_llm_answers(expe):
    """Coerce any answer.llm_answer that is a plain dict into an LLMAnswer, so
    Expe.stats()/get_name() (which access `.name`) don't crash. Safe no-op for
    answers whose llm_answer is already an object or None."""
    from ragtime.expe import LLMAnswer
    for qa in expe:
        if not (qa and qa.answers and qa.answers.items):
            continue
        for a in qa.answers.items:
            la = getattr(a, 'llm_answer', None)
            if isinstance(la, dict):
                try:
                    a.llm_answer = LLMAnswer(**la)
                except Exception:
                    # Last resort: keep only a name so stats() works.
                    a.llm_answer = LLMAnswer(name=str(la.get('name', '')) or None)


def build_debug_excel(expe, name):
    """Build a debug .xlsx (question / answer / chunk_1..N) from a retrieved
    Expe, for the user to inspect when they stop at the checkpoint. Returns the
    file path. Uses openpyxl (a package dependency)."""
    from openpyxl import Workbook
    from app.infra.storage import TEMP_FOLDER

    rows = []
    max_chunks = 0
    for qa in expe:
        q = qa.question.text if qa and qa.question else ''
        ans = ''
        if qa and qa.answers and qa.answers.items:
            ans = qa.answers.items[0].text or ''
        chunk_texts = [c.text for c in qa.chunks.items] if (qa and qa.chunks and qa.chunks.items) else []
        max_chunks = max(max_chunks, len(chunk_texts))
        rows.append((q, ans, chunk_texts))

    wb = Workbook()
    ws = wb.active
    ws.title = 'search_debug'
    header = ['question', 'answer'] + [f'chunk_{i+1}' for i in range(max_chunks)]
    ws.append(header)
    for q, ans, chunk_texts in rows:
        padded = chunk_texts + [''] * (max_chunks - len(chunk_texts))
        ws.append([q, ans] + padded)

    os.makedirs(TEMP_FOLDER, exist_ok=True)
    safe_name = ''.join(ch for ch in str(name) if ch.isalnum() or ch in ('-', '_')) or 'experiment'
    out_path = TEMP_FOLDER / f'{safe_name}_search_debug.xlsx'
    wb.save(out_path)
    return out_path


def run_experiment(config):
    """Execute the experiment synchronously. Returns the output path."""
    expe = build_expe(config)

    if not config['withCSV']:
        models = config['answerGenerationModels']
        use_retriever = config.get('useRetriever', False)
        retriever_type = config.get('retrieverType')

        if 'Albert_LLM' in models:
            use_retriever = True
            expe.meta['retriever_name'] = 'Albert_LLM (built-in retriever)'
        elif not use_retriever:
            expe.meta['retriever_name'] = 'No retriever'

        logging.info(f"Generating answers with models: {models}")
        reasoning = config.get('reasoning')
        reasoning_effort = config.get('reasoningEffort')
        generator = AnswerGeneratorService(models, use_retriever=use_retriever, retriever_type=retriever_type, reasoning=reasoning, reasoning_effort=reasoning_effort)
        expe = generator.generate_answers(expe)

    if config['evaluateAnswers']:
        logging.info(f"Evaluating answers with model: {config['evaluationModel']}")
        evaluator = EvaluationService(config['evaluationModel'])
        expe = evaluator.evaluate_answers(expe)

    if config['evaluateChunks']:
        logging.info(f"Evaluating chunks with model: {config['evaluationModel']}")
        evaluator = EvaluationService(config['evaluationModel'])
        expe = evaluator.evaluate_chunks(expe)

    # Record what was requested so the results UI can distinguish "chunk eval
    # not requested" from "requested but nothing to evaluate" (0 hallu/missing).
    expe.meta['evaluate_answers'] = bool(config.get('evaluateAnswers', True))
    expe.meta['evaluate_chunks'] = bool(config.get('evaluateChunks', False))

    # See _normalize_llm_answers: chunk eval can leave dict llm_answers that
    # crash Expe.stats() on save. Normalize before saving.
    _normalize_llm_answers(expe)

    return expe.save_to_json(path=EVALS_FOLDER / config['name'])


class _JobLogHandler(logging.Handler):
    def __init__(self, job_id):
        super().__init__(level=logging.INFO)
        self.job_id = job_id
        self.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))

    def emit(self, record):
        try:
            job_store.append_log(self.job_id, self.format(record))
        except Exception:
            pass  # never let log capture break the experiment


def _run_job(app, job_id, config):
    handler = _JobLogHandler(job_id)
    # ragtime.config.logger is a LoggerAdapter around the named stdlib
    # logger "ragtime_logger" — handlers attach to the underlying logger.
    package_logger = logging.getLogger('ragtime_logger')
    package_logger.addHandler(handler)
    with app.app_context():
        from app.services import key_service
        key_service.ensure_fresh()
        job_store.update_job(job_id, status='running',
                             started_at=datetime.now().isoformat())
        job_store.append_log(job_id, f"Starting experiment '{config.get('name', '')}'")
        try:
            if _is_search_retriever(config):
                # Search flow: phase 1 retrieves answers + chunks, then pauses
                # for human review before any evaluation is launched. The token
                # and folder id come from Profile settings (the APIKey table,
                # pushed into os.environ by key_service.ensure_fresh() above) —
                # they never travel through the frontend request, and are never
                # logged or stored.
                import os as _os
                from app.services import review_store, search_service
                token = _os.environ.get(search_service.SEARCH_TOKEN_KEY, '')
                folder_id = _os.environ.get(search_service.SEARCH_FOLDER_KEY) or None

                # No log callback: run_search_retrieval logs through
                # ragtime_logger, which the _JobLogHandler above already
                # captures for the job (and which also reaches Docker output) —
                # the same single channel as answer/eval generation. Passing an
                # append_log callback too would double each line in the job log.
                expe = run_search_phase1(config, token, folder_id)
                review_store.save_pending(job_id, expe.model_dump_json(), config)
                job_store.append_log(job_id, 'Retrieval complete — review the answers and chunks, then launch the evaluation.')
                job_store.update_job(job_id, status='awaiting_review',
                                     finished_at=datetime.now().isoformat())
            else:
                output_path = run_experiment(config)
                job_store.append_log(job_id, 'Experiment completed successfully')
                job_store.update_job(job_id, status='done',
                                     results_path=str(output_path),
                                     results_name=os.path.basename(str(output_path)),
                                     finished_at=datetime.now().isoformat())
        except Exception as e:
            logging.exception('Experiment job failed')
            job_store.append_log(job_id, f'ERROR: {e}')
            job_store.update_job(job_id, status='failed', error=str(e),
                                 finished_at=datetime.now().isoformat())
        finally:
            package_logger.removeHandler(handler)


def _run_phase2_job(app, job_id):
    """Evaluate a reviewed (retrieved) experiment: load the pending Expe, run
    the evaluation, save results, mark done. Used after the user approves the
    checkpoint."""
    from ragtime.expe import Expe
    handler = _JobLogHandler(job_id)
    package_logger = logging.getLogger('ragtime_logger')
    package_logger.addHandler(handler)
    with app.app_context():
        from app.services import key_service, review_store
        key_service.ensure_fresh()
        pending = review_store.load_pending(job_id)
        if pending is None:
            job_store.update_job(job_id, status='failed',
                                 error='No reviewed data found (it may have expired).',
                                 finished_at=datetime.now().isoformat())
            package_logger.removeHandler(handler)
            return
        job_store.update_job(job_id, status='running',
                             started_at=datetime.now().isoformat())
        job_store.append_log(job_id, 'Evaluation approved — starting evaluation')
        try:
            cfg = pending['config']
            expe = Expe()
            expe.load_from_dict(pending['expe'])
            expe.meta['validation_set'] = cfg.get('name')
            expe.meta['retriever_name'] = 'Search'
            output_path = run_evaluation_phase2(expe, cfg)
            review_store.discard_pending(job_id)
            job_store.append_log(job_id, 'Experiment completed successfully')
            job_store.update_job(job_id, status='done',
                                 results_path=str(output_path),
                                 results_name=os.path.basename(str(output_path)),
                                 finished_at=datetime.now().isoformat())
        except Exception as e:
            logging.exception('Evaluation job failed')
            job_store.append_log(job_id, f'ERROR: {e}')
            job_store.update_job(job_id, status='failed', error=str(e),
                                 finished_at=datetime.now().isoformat())
        finally:
            package_logger.removeHandler(handler)


def submit_job(app, config):
    job = job_store.create_job(config.get('name', 'experiment'))
    _executor.submit(_run_job, app, job['id'], config)
    return job


def submit_evaluation_job(app, job_id):
    """Kick off phase 2 (evaluation) for a job that is awaiting review."""
    _executor.submit(_run_phase2_job, app, job_id)
    return job_store.read_job(job_id)
