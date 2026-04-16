import json
import logging
import os
import sys
import traceback
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for the ATS application."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Merge extra fields attached by the request logging middleware
        for field in (
            "request_id",
            "method",
            "path",
            "query_params",
            "handler",
            "handler_file",
            "user_email",
            "status_code",
            "duration_ms",
        ):
            value = getattr(record, field, None)
            if value is not None:
                log_entry[field] = value

        # Include full stack trace when exc_info is present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_entry)


def setup_logging():
    """Configure the 'ats' logger with structured JSON output to stdout and logs/ folder."""
    formatter = JSONFormatter()

    # Console handler — stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # File handler — rotating log files in backend/logs/
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, "backend.log"),
        maxBytes=5 * 1024 * 1024,  # 5 MB per file
        backupCount=5,
    )
    file_handler.setFormatter(formatter)

    app_logger = logging.getLogger("ats")
    # Prevent duplicate handlers when uvicorn --reload re-runs setup
    if app_logger.handlers:
        app_logger.handlers.clear()
    app_logger.setLevel(logging.INFO)
    app_logger.addHandler(console_handler)
    app_logger.addHandler(file_handler)
    app_logger.propagate = False

    # Quiet down SQLAlchemy's verbose SQL echo
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return app_logger
