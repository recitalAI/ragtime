import os

# Use LiteLLM's bundled (local) model-cost map instead of fetching it from
# GitHub at startup. In a locked-down container the remote fetch times out on
# the SSL handshake and prints several noisy warnings before falling back to
# the local copy anyway; forcing local skips the timeout and the noise. Must
# be set before litellm is first imported (directly or via the ragtime
# package), so it sits at the very top of the app package. The local map
# already contains every model we price (OpenAI/Anthropic/Mistral); OVH prices
# are registered separately at runtime.
os.environ.setdefault('LITELLM_LOCAL_MODEL_COST_MAP', 'True')

from flask import Flask
from flask_cors import CORS
from config import Config
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from app.models import db


def create_app(config_class=Config):
    load_dotenv()
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config_class)

    # Store the Config class in app.config
    app.config['Config'] = config_class

    db.init_app(app)

    # Set up logging
    if not os.path.exists('logs'):
        try:
            os.mkdir('logs')
        except:
            pass
    file_handler = RotatingFileHandler('logs/ragtime.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)

    # HTTP layer: one focused blueprint per resource (app/api/*), all under
    # /api. The former routes.py monolith has been split into these modules;
    # the parallel flask-smorest layer (app/apis) was removed in Phase 1.
    from app.api import blueprints
    for bp in blueprints:
        app.register_blueprint(bp)

    with app.app_context():
        db.create_all()
        config_class.init_app(app, db)

    # NOTE (B4 fix): the per-request .env reload + DB query that used to run
    # in a before_request hook is gone. Keys are synced DB -> env at startup
    # (config_class.init_app above) and re-applied at the points that consume
    # them: key save (app/api/keys.py), generation endpoints, and job start
    # (key_service.ensure_fresh()).

    # app.logger records were printed twice: once by Flask's default stderr
    # handler and once via propagation to the root logger (configured by an
    # imported library). Our handlers are explicit — stop the propagation.
    app.logger.propagate = False

    @app.route('/test')
    def test_route():
        # Docker healthcheck target — kept silent so the 30s probe does not
        # flood the logs.
        return 'Test route is working'

    return app
