from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import os
from app.models import db
from .log_capture import log_capture

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
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/ragtime.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)

    from app.routes import main
    app.register_blueprint(main)

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