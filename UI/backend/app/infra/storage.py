"""Single source of truth for the on-disk data layout, plus safe filename
resolution (S1 fix): every filename coming from a request is resolved inside
its base folder and rejected if it escapes it (path separators, '..',
absolute paths). No endpoint should build file paths on its own.
"""
from pathlib import Path

# storage.py lives at app/infra/ — the data root is <backend>/files.
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

FILES_FOLDER = _BACKEND_DIR / 'files'
VALIDATION_SETS_FOLDER = FILES_FOLDER / 'validation_sets'
EVALS_FOLDER = FILES_FOLDER / 'evaluation_results'
TEMP_FOLDER = FILES_FOLDER / 'temp'


def safe_path(folder, filename):
    """Resolve `filename` inside `folder`, rejecting names that escape it
    (path separators, '..', absolute paths). Returns a Path or raises ValueError."""
    if not filename or not isinstance(filename, str):
        raise ValueError('A filename must be provided')
    candidate = (Path(folder) / filename).resolve()
    base = Path(folder).resolve()
    if base not in candidate.parents:
        raise ValueError(f'Invalid filename: "{filename}"')
    return candidate
