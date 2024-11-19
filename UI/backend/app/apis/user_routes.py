from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import current_app
from app.models import APIKey, db
from .models.user_models import (
    ApiKeySchema,
    ApiKeysUpdateSchema,
    ApiKeyAvailabilitySchema,
    MessageResponseSchema,
    DefaultApiKeySchema
)
import os
from dotenv import find_dotenv, set_key, unset_key, load_dotenv

user_bp = Blueprint(
    'user_api',
    'User operations',
    url_prefix='/api/user'
)

@user_bp.route('/api-keys')
class ApiKeys(MethodView):
    @user_bp.response(200, ApiKeySchema(many=True))
    def get(self):
        """Get all API keys
        
        Returns a list of all stored API keys.
        ---
        Returns:
            A list of API keys with their names and values
        """
        keys = APIKey.query.all()
        return [{"name": key.name, "value": key.value} for key in keys]

    @user_bp.arguments(ApiKeysUpdateSchema)
    @user_bp.response(200, MessageResponseSchema)
    def post(self, data):
        """Update API keys
        
        Handles multiple operations in one request:
        - Adds new API keys
        - Updates existing API keys
        - Deletes specified API keys
        ---
        Parameters:
            - apiKeys (list): List of API keys to add/update
            - deletedKeys (list): List of API key names to delete
        """
        try:
            new_keys = data.get('apiKeys', [])
            deleted_keys = data.get('deletedKeys', [])

            # Remove existing keys from database
            APIKey.query.filter_by(user_id='default').delete()

            # Add new keys to database
            for key in new_keys:
                new_key = APIKey(
                    name=key['name'],
                    value=key['value'],
                    user_id='default'
                )
                db.session.add(new_key)

            db.session.commit()

            # Handle .env file updates
            env_path = os.path.join(current_app.root_path, '..', '.env')
            dotenv_file = find_dotenv(env_path)

            # Delete keys from .env
            for key_name in deleted_keys:
                unset_key(dotenv_file, key_name)
                if key_name in os.environ:
                    del os.environ[key_name]

            # Add/Update keys in .env
            for key in new_keys:
                set_key(dotenv_file, key['name'], key['value'])
                os.environ[key['name']] = key['value']

            load_dotenv(dotenv_file, override=True)

            # Update Config object
            Config = current_app.config.get('Config')
            if Config:
                Config.update_config_with_user_keys()

            return {"message": "API keys saved and deleted successfully"}
        except Exception as e:
            db.session.rollback()
            abort(500, message=str(e))

@user_bp.route('/api-keys/availability')
class ApiKeyAvailability(MethodView):
    @user_bp.response(200, ApiKeyAvailabilitySchema)
    def get(self):
        """Check API key availability
        
        Returns the availability status of OpenAI and Mistral API keys.
        ---
        Returns:
            Status of OpenAI and Mistral API keys (boolean values)
        """
        Config = current_app.config.get('Config')
        openai_key = Config.get_openai_api_key()
        mistral_key = Config.get_mistral_api_key()
        
        return {
            'openai': bool(openai_key),
            'mistral': bool(mistral_key)
        }

@user_bp.route('/api-keys/refresh')
class ApiKeyRefresh(MethodView):
    @user_bp.response(200, ApiKeyAvailabilitySchema)
    def post(self):
        """Refresh API key availability
        
        Updates the Config with latest API keys and returns their availability status.
        ---
        Returns:
            Updated status of OpenAI and Mistral API keys
        """
        Config = current_app.config.get('Config')
        if Config:
            Config.update_config_with_user_keys()
        
        openai_key = Config.get_openai_api_key()
        mistral_key = Config.get_mistral_api_key()
        
        return {
            'openai': bool(openai_key),
            'mistral': bool(mistral_key)
        }

@user_bp.route('/api-keys/default/<key_name>')
class DefaultApiKey(MethodView):
    @user_bp.response(200, DefaultApiKeySchema)
    def get(self, key_name):
        """Get default value for a specific API key
        
        Retrieves the default value for a given API key name from environment variables.
        ---
        Parameters:
            - key_name (str): Name of the API key
        Returns:
            Default value for the specified API key
        """
        default_value = os.getenv(key_name, '')
        return {"value": default_value}