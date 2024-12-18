from datetime import datetime
import re
import os
import shutil

class LogCapture:
    def __init__(self, log_file_path='/usr/local/bin/logs/logs.txt'):
        self.log_file_path = log_file_path
        self.start_time = datetime.now()
        self.last_log_time = None
        
        # Setup backup path in app logs directory
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.backup_path = os.path.join(current_dir, 'logs', 'experiment_logs.txt')
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(self.backup_path), exist_ok=True)

    def get_logs(self, last_timestamp=None):
        with open(self.log_file_path, 'r') as f:
            logs = f.readlines()
            
        # Create backup
        with open(self.backup_path, 'w') as f:
            f.writelines(logs)

        filtered_logs = []
        last_timestamp = last_timestamp or self.start_time

        for log in logs:
            log_time = self.parse_log_time(log)
            if log_time and log_time > last_timestamp:
                filtered_logs.append(log.strip())
                last_timestamp = log_time

        if filtered_logs:
            self.last_log_time = last_timestamp

        return filtered_logs, last_timestamp.isoformat() if last_timestamp else None

    def parse_log_time(self, log_line):
        match = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\]', log_line)
        if match:
            return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S,%f')
        return None

    def is_experiment_complete(self):
        if not self.last_log_time:
            return False
        time_since_last_log = datetime.now() - self.last_log_time
        return time_since_last_log.total_seconds() > 30

log_capture = LogCapture()