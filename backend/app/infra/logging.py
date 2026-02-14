import logging
import logging.config
import sys
from typing import Dict, Any
import json

from .config import settings


class StructuredFormatter(logging.Formatter):
    """
    Structured logging formatter that outputs JSON format.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "extra") and record.extra:
            log_entry["extra"] = record.extra

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


class RequestContextFilter(logging.Filter):
    """
    Adds request context to log records.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # Add default request context if not present
        if not hasattr(record, "request_id"):
            record.request_id = "unknown"
        if not hasattr(record, "user_id"):
            record.user_id = "anonymous"

        return True


def setup_logging() -> None:
    """
    Configure logging based on environment settings.
    """
    log_level = getattr(settings, "log_level", "INFO").upper()
    log_format = getattr(settings, "log_format", "standard")  # "standard" or "json"

    # Determine log level
    numeric_level = getattr(logging, log_level, logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Set formatter based on environment
    if log_format == "json":
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler.setFormatter(formatter)

    # Add request context filter
    context_filter = RequestContextFilter()
    console_handler.addFilter(context_filter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    configure_app_loggers(numeric_level)

    # Log configuration
    logging.info(
        "Logging configured",
        extra={
            "log_level": log_level,
            "log_format": log_format,
            "handlers": len(root_logger.handlers)
        }
    )


def configure_app_loggers(level: int) -> None:
    """
    Configure application-specific loggers.
    """
    # Set specific log levels for different components
    logger_configs = {
        "app.services": level,
        "app.infra": level,
        "app.repositories": level,
        "uvicorn.access": logging.WARNING,  # Reduce noise from access logs
        "requests": logging.WARNING,        # Reduce requests library noise
        "urllib3": logging.WARNING,         # Reduce urllib3 noise
    }

    for logger_name, logger_level in logger_configs.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(logger_level)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    """
    return logging.getLogger(name)


# Initialize logging when module is imported
setup_logging()

