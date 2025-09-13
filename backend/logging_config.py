"""
Logging configuration for F1 Undercut Simulation backend.

This module configures structured logging with JSON formatter using structlog.
It provides request correlation IDs and proper log formatting for production.
"""

import os
import sys
import logging
import structlog
from typing import Any, Dict


def configure_logging() -> None:
    """Configure structured logging with JSON formatter."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level),
    )
    
    # Remove default handlers to avoid duplicate logs
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Add log level to event dict
            structlog.processors.add_log_level,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="iso"),
            # Add request ID if available
            _add_request_id,
            # JSON formatter for production
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level)
        ),
        context_class=dict,
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _add_request_id(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add request ID to log entries if available in context."""
    # This will be populated by our middleware
    request_id = structlog.contextvars.get_contextvars().get("request_id")
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a configured structlog logger."""
    return structlog.get_logger(name)