"""Structured logging configuration for the ETL Dashboard."""

import logging
import sys
from typing import Any, Dict, List

import structlog
from structlog.types import EventDict

from .config import settings


def add_severity_level(
    logger: Any, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add severity level to log entries."""
    if method_name == "info":
        event_dict["severity"] = "INFO"
    elif method_name == "warning":
        event_dict["severity"] = "WARNING"
    elif method_name == "error":
        event_dict["severity"] = "ERROR"
    elif method_name == "debug":
        event_dict["severity"] = "DEBUG"
    elif method_name == "critical":
        event_dict["severity"] = "CRITICAL"
    else:
        event_dict["severity"] = "INFO"

    return event_dict


def setup_logging() -> None:
    """Configure structured logging for the application."""
    import os
    from pathlib import Path

    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "etl.log"

    # Configure standard library logging with file handler
    file_handler = logging.FileHandler(str(log_file), mode='a', encoding='utf-8')
    file_handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))

    # Clear any existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    logging.basicConfig(
        format="%(message)s",
        handlers=[file_handler, console_handler],
        level=getattr(logging, settings.log_level.upper()),
        force=True  # Force reconfiguration
    )

    # Configure structlog
    processors: List[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        add_severity_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.log_format.lower() == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend(
            [
                structlog.dev.ConsoleRenderer(colors=True),
            ]
        )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper())
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),  # FIXED: Use stdlib logger factory
        cache_logger_on_first_use=True,
    )


class ETLLogger:
    """ETL-specific logger with message collection for frontend display."""

    def __init__(self):
        self.logger = structlog.get_logger()
        self.messages: List[Dict[str, Any]] = []

    def info(self, message: str, **kwargs) -> None:
        """Log info message and store for frontend."""
        self.logger.info(message, **kwargs)
        self.messages.append({"level": "info", "message": message, "data": kwargs})

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message and store for frontend."""
        self.logger.warning(message, **kwargs)
        self.messages.append({"level": "warning", "message": message, "data": kwargs})

    def error(self, message: str, **kwargs) -> None:
        """Log error message and store for frontend."""
        self.logger.error(message, **kwargs)
        self.messages.append({"level": "error", "message": message, "data": kwargs})

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message and store for frontend."""
        self.logger.debug(message, **kwargs)
        self.messages.append({"level": "debug", "message": message, "data": kwargs})

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all collected messages for frontend display."""
        return self.messages.copy()

    def clear_messages(self) -> None:
        """Clear collected messages."""
        self.messages.clear()


# Initialize logging
setup_logging()

# Get logger instance
logger = structlog.get_logger()
