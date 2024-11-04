import logging
import os
import sys
import boto3
from google.cloud import logging as gcp_logging
from logging.handlers import RotatingFileHandler, SysLogHandler

# Global Logger Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = 'app.log'
LOG_MAX_BYTES = 1024 * 1024 * 10  # 10MB
LOG_BACKUP_COUNT = 5

class LogConfig:
    def __init__(self):
        self.logger = logging.getLogger("AppLogger")
        self.logger.setLevel(LOG_LEVEL)

        formatter = logging.Formatter(LOG_FORMAT)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LOG_LEVEL)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler with log rotation
        file_handler = RotatingFileHandler(LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT)
        file_handler.setLevel(LOG_LEVEL)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Add CloudWatch Logging
        if os.getenv("USE_CLOUDWATCH"):
            self.add_cloudwatch_logging()

        # Add Google Cloud Logging
        if os.getenv("USE_GCP_LOGGING"):
            self.add_gcp_logging()

        # Add Syslog Handler
        if os.getenv("USE_SYSLOG"):
            syslog_handler = SysLogHandler(address='/dev/log')
            syslog_handler.setFormatter(formatter)
            syslog_handler.setLevel(LOG_LEVEL)
            self.logger.addHandler(syslog_handler)

    def add_cloudwatch_logging(self):
        """Add AWS CloudWatch logging"""
        log_group = os.getenv("CLOUDWATCH_LOG_GROUP", "app-log-group")
        log_stream = os.getenv("CLOUDWATCH_LOG_STREAM", "app-log-stream")
        region = os.getenv("AWS_REGION", "us-east-1")
        
        session = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=region
        )
        logs_client = session.client('logs')

        try:
            logs_client.create_log_group(logGroupName=log_group)
        except logs_client.exceptions.ResourceAlreadyExistsException:
            pass

        try:
            logs_client.create_log_stream(logGroupName=log_group, logStreamName=log_stream)
        except logs_client.exceptions.ResourceAlreadyExistsException:
            pass

        cw_handler = CloudWatchHandler(log_group, log_stream, logs_client)
        cw_handler.setLevel(LOG_LEVEL)
        self.logger.addHandler(cw_handler)

    def add_gcp_logging(self):
        """Add Google Cloud Logging"""
        gcp_client = gcp_logging.Client()
        gcp_handler = gcp_client.get_default_handler()
        gcp_handler.setLevel(LOG_LEVEL)
        self.logger.addHandler(gcp_handler)

    def get_logger(self):
        return self.logger

class CloudWatchHandler(logging.Handler):
    """Custom handler for AWS CloudWatch logging"""
    def __init__(self, log_group, log_stream, logs_client):
        super().__init__()
        self.log_group = log_group
        self.log_stream = log_stream
        self.logs_client = logs_client
        self.sequence_token = None

    def emit(self, record):
        try:
            msg = self.format(record)
            log_event = {
                'logGroupName': self.log_group,
                'logStreamName': self.log_stream,
                'logEvents': [
                    {
                        'timestamp': int(record.created * 1000),
                        'message': msg
                    }
                ],
            }

            if self.sequence_token:
                log_event['sequenceToken'] = self.sequence_token

            response = self.logs_client.put_log_events(**log_event)
            self.sequence_token = response['nextSequenceToken']
        except Exception as e:
            print(f"Failed to log to CloudWatch: {e}")

def setup_logging():
    """Set up logging based on environment configuration"""
    log_config = LogConfig()
    return log_config.get_logger()

if __name__ == '__main__':
    logger = setup_logging()

    # Log messages
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")