import logging
import sys
from pythonjsonlogger import jsonlogger
from datetime import datetime, timezone
from globals.utils.context import get_log_context
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from queue import Queue
import os

class LogsConfig(jsonlogger.JsonFormatter):
    """Custom JSON logging formatter"""
    def parse(self):
        """Define the order of fields"""
        return [
            "@timestamp",
            "level",
            "logger_name",
            "thread_name",
            "host_from",
            "path",
            "method",
            "reference_id",
            "user_id",  
            "message",
        ]

    def format(self, record):
        """Formats the log record in JSON format"""
        context = get_log_context()
        current_time = datetime.now(timezone.utc)
        ordered_fields = {
            "@timestamp": current_time.isoformat(),
            "level": record.levelname,
            "logger_name": record.name,
            "thread_name": record.threadName,
            "host_from": context.get("host_from", "N/A"),
            "path": context.get("path", "N/A"),
            "method": context.get("method", "N/A"),
            "reference_id": context.get("reference_id", "N/A"),
            "user_id": context.get("user_id", "N/A"),  
            "message": record.msg,
        }

        record.__dict__.update(ordered_fields)
        return super().format(record)
    

def get_async_logger(name="MyLogger", process_name=None):
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)
    
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    log_dir = os.path.join(root_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Create separate log file per process
    if process_name is None:
        # Auto-detect process type
        if 'celery' in sys.argv[0].lower() or 'worker' in ' '.join(sys.argv):
            process_name = 'celery'
        else:
            process_name = 'fastapi'
    
    log_file = f"app_{process_name}.log"
    log_path = os.path.join(log_dir, log_file)

    # Formatter
    formatter = LogsConfig()

    # Queue for async logging
    log_queue = Queue(-1)
    queue_handler = QueueHandler(log_queue)
    queue_handler.setFormatter(formatter)
    logger.addHandler(queue_handler)

    # File handler with rotation (rotate at 10MB, keep 5 files)
    file_handler = RotatingFileHandler(
        log_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)

    # Optional: Console logging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Start listener with file + console handlers
    listener = QueueListener(log_queue, file_handler, console_handler)
    listener.start()

    return logger
       

# logger = get_logger("default_logger/billing-system")
logger = get_async_logger("async_logger/billing-system")


