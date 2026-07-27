from datetime import datetime

from flask import Blueprint, jsonify, request

from app.infra.log_capture import log_capture

logs_bp = Blueprint('logs', __name__, url_prefix='/api')


@logs_bp.route('/live-logs', methods=['GET'])
def get_live_logs():
    last_timestamp = request.args.get('lastTimestamp')
    if last_timestamp:
        last_timestamp = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))

    logs, new_last_timestamp = log_capture.get_logs(last_timestamp)

    return jsonify({
        'logs': logs,
        'lastTimestamp': new_last_timestamp,
        'isComplete': log_capture.is_experiment_complete()
    })
