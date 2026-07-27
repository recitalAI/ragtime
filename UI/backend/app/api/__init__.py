"""HTTP layer: one focused blueprint per resource, all under /api.

Route handlers validate input, delegate to services/domain, and shape the
JSON response. Filesystem access goes through app.infra.storage.
"""
from .experiments import experiments_bp
from .generation import generation_bp
from .jobs import jobs_bp
from .keys import keys_bp
from .logs import logs_bp
from .models_info import models_info_bp
from .validation_sets import validation_sets_bp

blueprints = [
    logs_bp,
    keys_bp,
    validation_sets_bp,
    generation_bp,
    jobs_bp,
    experiments_bp,
    models_info_bp,
]
