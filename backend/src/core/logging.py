"""Structured logging configuration."""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
import structlog


def setup_logging(log_dir: str = "data/logs", log_level: str = "INFO") -> None:
    """
    Configure structured logging with ISO 8601 timestamps and JSON context.

    Args:
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create log directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

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


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


def log_pipeline_stage(stage_name: str):
    """
    Decorator to log pipeline stage execution with input/output counts.

    Args:
        stage_name: Name of the pipeline stage

    Returns:
        Decorator function
    """
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            logger.info(f"{stage_name} started", stage=stage_name)

            try:
                result = func(*args, **kwargs)

                # Calculate counts
                input_count = len(args[0]) if args and hasattr(args[0], "__len__") else 0
                output_count = len(result) if result and hasattr(result, "__len__") else 0

                logger.info(
                    f"{stage_name} completed",
                    stage=stage_name,
                    input_count=input_count,
                    output_count=output_count,
                )

                return result
            except Exception as e:
                logger.error(
                    f"{stage_name} failed",
                    stage=stage_name,
                    error=str(e),
                    exc_info=True,
                )
                raise

        return wrapper
    return decorator
