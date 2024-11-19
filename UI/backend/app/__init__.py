from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import os
from app.models import db
from .log_capture import log_capture
from flask_smorest import Api

def create_app(config_class=Config):
    load_dotenv()
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config_class)
    
    # Add Swagger config while keeping original functionality
    app.config.update({
        "API_TITLE": "Ragtime API",
        "API_VERSION": "1.0",
        "OPENAPI_VERSION": "3.0.2",
        "OPENAPI_URL_PREFIX": "",
        "OPENAPI_SWAGGER_UI_PATH": "/docs",
        "OPENAPI_SWAGGER_UI_URL": "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    })

    # Initialize API
    api = Api(app)
    
    # Store the Config class in app.config
    app.config['Config'] = config_class

    db.init_app(app)

    # Set up logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/ragtime.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)

    # Register original routes first
    from app.routes import main
    app.register_blueprint(main)

    # Register Swagger documentation (optional routes)
    from app.apis.user_routes import user_bp
    from app.apis.validation_routes import validation_bp
    from app.apis.experiment_routes import experiment_bp
    api.register_blueprint(user_bp, name='user-api')
    api.register_blueprint(validation_bp, name='validation_api')
    api.register_blueprint(experiment_bp, name='experiment_api')

    with app.app_context():
        db.create_all()
        config_class.init_app(app, db)

    @app.before_request
    def reload_env():
        load_dotenv(override=True)
        config_class.update_config_with_user_keys()

    @app.route('/test')
    def test_route():
        app.logger.info('Test route accessed')
        return 'Test route is working'

    @app.route('/api/live-logs')
    def live_logs():
        return jsonify({'logs': log_capture.get_logs()})

    return app