"""Logging configuration using structlog."""

import logging
import logging.handlers
from pathlib import Path

import structlog

from ..config.settings import LoggingConfig


def setup_logging(config: LoggingConfig) -> None:
    """
    Configure structured logging.

    Args:
        config: Logging configuration
    """
    # Ensure log directory exists
    if config.file:
        log_path = Path(config.file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure handlers
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if config.file:
        handlers.append(
            logging.handlers.RotatingFileHandler(
                config.file,
                maxBytes=config.max_size_mb * 1024 * 1024,
                backupCount=config.backup_count,
            )
        )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, config.level.upper()),
        handlers=handlers,
    )
