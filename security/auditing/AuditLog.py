import os
import logging
from datetime import datetime
from enum import Enum
import json
import hashlib

# Audit Action Types
class AuditActionType(Enum):
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'
    ACCESS = 'ACCESS'

# Configuring logging format and level
logging.basicConfig(filename='audit_log.txt',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

class AuditLog:
    def __init__(self, log_dir='logs/'):
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def generate_hash(self, data):
        """
        Generates a SHA256 hash for data integrity verification.
        """
        return hashlib.sha256(data.encode()).hexdigest()

    def log_event(self, action: AuditActionType, user_id: str, details: dict):
        """
        Logs the audit event into the log file with action, user, timestamp and details.
        """
        timestamp = datetime.utcnow().isoformat()
        event_data = {
            'timestamp': timestamp,
            'action': action.value,
            'user_id': user_id,
            'details': details,
            'hash': self.generate_hash(f"{timestamp}{user_id}{action.value}")
        }
        self.write_log(event_data)

    def write_log(self, data):
        """
        Writes the audit log to a file and stores a hash for integrity check.
        """
        log_file_path = os.path.join(self.log_dir, f'audit_log_{datetime.utcnow().date()}.txt')
        with open(log_file_path, 'a') as log_file:
            log_file.write(json.dumps(data) + '\n')
        logging.info(f"Audit log written for action: {data['action']} by user: {data['user_id']}")

    def read_logs(self, date=None):
        """
        Reads audit logs for a specific date. If date is not provided, it reads today's logs.
        """
        if date is None:
            date = datetime.utcnow().date()
        log_file_path = os.path.join(self.log_dir, f'audit_log_{date}.txt')
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as log_file:
                return log_file.readlines()
        else:
            logging.warning(f"No audit log found for date: {date}")
            return []

    def verify_log_integrity(self, date=None):
        """
        Verifies the integrity of the audit logs by checking the hashes.
        """
        logs = self.read_logs(date)
        for log_entry in logs:
            log_data = json.loads(log_entry)
            expected_hash = self.generate_hash(f"{log_data['timestamp']}{log_data['user_id']}{log_data['action']}")
            if expected_hash != log_data['hash']:
                logging.error(f"Integrity check failed for log entry: {log_data}")
                return False
        logging.info("All logs passed integrity check.")
        return True

# Usage
if __name__ == "__main__":
    audit_logger = AuditLog()

    # Logging some events
    audit_logger.log_event(AuditActionType.LOGIN, 'user_123', {'ip': '192.168.1.1'})
    audit_logger.log_event(AuditActionType.CREATE, 'user_123', {'object_id': 'obj_001', 'description': 'Created a new object'})
    audit_logger.log_event(AuditActionType.LOGOUT, 'user_123', {'session_id': 'sess_456'})

    # Read logs
    logs = audit_logger.read_logs()
    for log in logs:
        print(log)

    # Verify the integrity of the logs
    is_valid = audit_logger.verify_log_integrity()
    print(f"Log integrity valid: {is_valid}")