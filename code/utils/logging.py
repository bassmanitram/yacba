"""Simple logging configuration for YACBA using envlog.

This module provides a minimal logging interface using envlog, which configures
Python's standard library logging from the PTHN_LOG environment variable.

The module provides a thin wrapper around stdlib logging to support structlog-style
keyword argument logging for backward compatibility.

Usage:
    from utils.logging import get_logger

    logger = get_logger(__name__)
    logger.info("Operation completed")
    logger.info("operation_completed", count=42, duration_ms=123)  # structlog-style
    logger.error("Operation failed")

Configuration via environment variable:
    # Set default level
    PTHN_LOG=info

    # Set module-specific levels
    PTHN_LOG=error,yacba.config=debug

    # Complex example with third-party suppression
    PTHN_LOG=error,yacba=info,strands_agent_factory=warn,strands_agents=warn
"""

import logging
from typing import Any

import envlog


class StructlogCompatLogger(logging.LoggerAdapter):
    """
    Logger adapter that provides structlog-style keyword argument support.

    Allows both traditional and structlog-style logging:
        logger.info("message %s", value)          # Traditional
        logger.info("event", key=value, foo=bar)  # structlog-style
    """

    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict]:
        """
        Process log message to support structlog-style kwargs.

        Extracts any custom kwargs and formats them into the message.
        """
        # Extract standard logging kwargs
        standard_keys = {"exc_info", "stack_info", "stacklevel", "extra"}
        custom_kwargs = {k: v for k, v in kwargs.items() if k not in standard_keys}
        standard_kwargs = {k: v for k, v in kwargs.items() if k in standard_keys}

        # If there are custom kwargs, format them into the message
        if custom_kwargs:
            # Build key=value pairs
            pairs = [f"{k}={v!r}" for k, v in custom_kwargs.items()]
            formatted_msg = f"{msg} [{', '.join(pairs)}]"
            return formatted_msg, standard_kwargs

        return msg, kwargs


def configure_logging() -> None:
    """
    Configure logging from PTHN_LOG environment variable.

    Uses envlog to parse RUST_LOG-style specifications and configure
    Python's standard library logging. Called automatically on import.

    All logging levels are controlled via PTHN_LOG. Examples:
        PTHN_LOG=error                           # All loggers at ERROR
        PTHN_LOG=error,yacba=debug               # YACBA at DEBUG, rest ERROR
        PTHN_LOG=error,strands_agent_factory=warn # Suppress strands to WARN
    """
    envlog.init(
        log_format="%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
        date_format="%Y-%m-%d %H:%M:%S",
    )


def get_logger(name: str) -> StructlogCompatLogger:
    """
    Get a logger for the given name with structlog-style support.

    Args:
        name: Logger name (typically __name__)

    Returns:
        StructlogCompatLogger instance that supports both traditional
        and structlog-style logging

    Example:
        logger = get_logger(__name__)
        logger.info("Application started")
        logger.debug("user_logged_in", user_id=123, session="abc")
    """
    base_logger = logging.getLogger(name)
    return StructlogCompatLogger(base_logger, {})


# Configure on import
configure_logging()
