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
    if not all(field in config for field in REQUIRED_FIELDS):
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


def build_expe(config):
    validation_set_data = config.get('validationSetData')
    if config.get('withCSV') and isinstance(validation_set_data, dict) and validation_set_data.get('items'):
        # Excel/CSV path: use the answers the user imported and matched.
        expe = Expe(json_dict=_normalize_csv_items(validation_set_data['items']))
    else:
        validation_set_path = safe_path(VALIDATION_SETS_FOLDER, config['validationSet'])
        if not validation_set_path.exists():
            raise ValueError(f'Validation set "{config["validationSet"]}" not found')
        expe = Expe(validation_set_path)

    expe.meta['validation_set'] = config['validationSet']
    expe.meta['retriever_name'] = config.get('retrieverType', 'Not used')
    return expe


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


def submit_job(app, config):
    job = job_store.create_job(config.get('name', 'experiment'))
    _executor.submit(_run_job, app, job['id'], config)
    return job
