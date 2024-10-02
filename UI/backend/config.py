import os
from dotenv import load_dotenv
from flask import current_app
import logging

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-key-for-development'
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'

    @classmethod
    def get_env_variable(cls, name):
        return os.environ.get(name)

    @property
    def LSA_USERNAME(self):
        return self.get_env_variable("LSA_USERNAME")

    @property
    def LSA_PASSWORD(self):
        return self.get_env_variable("LSA_PASSWORD")

    @classmethod
    def init_app(cls, app, db):
        cls.db = db
        cls.app = app
        with app.app_context():
            cls.update_config_with_user_keys()

    @classmethod
    def update_config_with_user_keys(cls):
        from app.models import APIKey

        with current_app.app_context():
            user_keys = APIKey.query.filter_by(user_id='default').all()
            for key in user_keys:
                os.environ[key.name] = key.value

    @classmethod
    def get_api_key(cls, key_name, user_id='default'):
        from app.models import APIKey

        with current_app.app_context():
            key = APIKey.query.filter_by(
                user_id=user_id, name=key_name).first()
            if key:
                return key.value

        env_value = os.environ.get(key_name)
        if env_value:
            return env_value

        return None

    @classmethod
    def get_openai_api_key(cls):
        return cls.get_api_key('OPENAI_API_KEY')

    @classmethod
    def get_mistral_api_key(cls):
        return cls.get_api_key('MISTRAL_API_KEY')

    @classmethod
    def get_custom_api_key(cls, key_name):
        return cls.get_api_key(key_name)
