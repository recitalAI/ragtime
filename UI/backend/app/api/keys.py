import logging
import os

from dotenv import load_dotenv, set_key
from flask import Blueprint, current_app, jsonify, request

from config import Config

from app.services import key_service

keys_bp = Blueprint('keys', __name__, url_prefix='/api')


@keys_bp.route('/user/save-env', methods=['POST'])
def save_to_env_file():
    try:
        key = request.json.get('key')
        value = request.json.get('value')
        if not key or value is None:
            return jsonify({'error': 'Key and value must be provided'}), 400

        env_path = os.path.join(current_app.root_path, '..', '.env')

        # Ensure the .env file exists
        if not os.path.exists(env_path):
            open(env_path, 'a').close()

        # Update or add the key-value pair
        set_key(env_path, key, value)

        # Reload the environment variables
        load_dotenv(env_path, override=True)

        return jsonify({'message': f'Environment variable {key} saved successfully'}), 200
    except Exception as e:
        current_app.logger.error(f"Error saving to .env file: {str(e)}")
        return jsonify({'error': str(e)}), 500


@keys_bp.route('/user/api-keys/refresh', methods=['POST'])
def refresh_api_keys():
    config_class = current_app.config.get('Config')
    if config_class:
        config_class.update_config_with_user_keys()

    openai_key = config_class.get_openai_api_key()
    mistral_key = config_class.get_mistral_api_key()

    return jsonify({
        'openai': bool(openai_key),
        'mistral': bool(mistral_key)
    }), 200


@keys_bp.route('/user/api-keys', methods=['GET'])
def get_api_keys():
    # Masked: plaintext secrets never leave the server. save_keys() resolves
    # a re-posted mask back to the stored value, so the settings page's
    # load -> save round trip keeps keys intact.
    return jsonify(key_service.list_keys_masked()), 200


# Maps a provider key (as used in the model catalog's `required_key`) to the
# environment variable that holds its credential.
_KEY_ENV = {
    'openai': 'OPENAI_API_KEY',
    'mistral': 'MISTRAL_API_KEY',
    'anthropic': 'ANTHROPIC_API_KEY',
    'ovh': 'OVH_API_KEY',
}


@keys_bp.route('/user/api-keys/availability', methods=['GET'])
def get_api_key_availability():
    # Data-driven: report availability for every provider key the catalog
    # actually requires (including OVH built-ins and any future provider),
    # so adding a provider needs no change here.
    from app.api.models_info import required_keys
    availability = {}
    for key in required_keys():
        env_name = _KEY_ENV.get(key, f'{key.upper()}_API_KEY')
        availability[key] = bool(Config.get_api_key(env_name))
    # Always include the core providers even if no model currently lists them.
    for key in ('openai', 'mistral'):
        availability.setdefault(key, bool(Config.get_api_key(_KEY_ENV[key])))
    return jsonify(availability), 200


@keys_bp.route('/user/api-keys', methods=['POST'])
def save_api_keys():
    data = request.json
    new_keys = data.get('apiKeys', [])
    deleted_keys = data.get('deletedKeys', [])

    key_service.save_keys(new_keys, deleted_keys)

    return jsonify({"message": "API keys saved and deleted successfully"}), 200


@keys_bp.route('/user/api-keys/default/<key_name>', methods=['GET'])
def get_default_api_key(key_name):
    # Masked for the same reason as the listing above.
    return jsonify({"value": key_service.mask(os.getenv(key_name, ''))}), 200
