from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, APIKey

api_keys = Blueprint('api_keys', __name__)

@api_keys.route('/api/user/api-keys', methods=['GET'])
@jwt_required()
def get_api_keys():
    user_id = get_jwt_identity()
    keys = APIKey.query.filter_by(user_id=user_id).all()
    return jsonify([{"name": key.name, "value": key.value} for key in keys]), 200

@api_keys.route('/api/user/api-keys', methods=['POST'])
@jwt_required()
def save_api_keys():
    user_id = get_jwt_identity()
    new_keys = request.json

    # Remove existing keys
    APIKey.query.filter_by(user_id=user_id).delete()

    # Add new keys
    for key in new_keys:
        new_key = APIKey(name=key['name'], value=key['value'], user_id=user_id)
        db.session.add(new_key)

    db.session.commit()
    return jsonify({"message": "API keys saved successfully"}), 200