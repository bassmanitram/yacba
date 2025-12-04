"""Logging configuration for YACBA.

This module configures dual-output logging:
- Interactive mode:
  - Console: Succinct, colored output to stderr (NO tracebacks by default)
  - File: Complete logs with timestamps and full tracebacks
- Headless mode:
  - Console: Full error output with tracebacks to stderr
  - File: Complete logs with timestamps and full tracebacks
- Debug mode (YACBA_SHOW_ALL_ERRORS=1):
  - Console: Full error output with tracebacks (even in interactive mode)
  - Shows suppressed errors
  - File: Complete logs with timestamps and full tracebacks

Usage:
    from utils.logging import configure_logging, get_logger
    from utils.session_utils import get_log_path

    # Early initialization (before session known)
    configure_logging(get_log_path(None), headless=False)

    # Later, after session is known
    configure_logging(get_log_path(session_name), headless=config.headless)

    # Use logger
    logger = get_logger(__name__)
    logger.info("Operation completed")
    logger.info("operation_completed", count=42, duration_ms=123)  # structlog-style

Configuration via environment variable:
    PTHN_LOG=info                    # Set default level
    PTHN_LOG=error,yacba.config=debug # Set module-specific levels
    YACBA_SHOW_ALL_ERRORS=1           # Show full tracebacks and suppressed errors on console
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any

import envlog
from utils.error_intelligence import ErrorIntelligenceFilter


class NoTracebackConsoleFormatter(logging.Formatter):
    """Formatter that adds color and suppresses tracebacks on console (interactive mode)."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[1;31m",  # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record):
        """Format log record with color, without traceback."""
        # Save and clear exc_info to prevent traceback output
        exc_info = record.exc_info
        exc_text = record.exc_text
        record.exc_info = None
        record.exc_text = None

        # Save original levelname
        original_levelname = record.levelname

        # Add color if terminal supports it
        if sys.stderr.isatty():
            color = self.COLORS.get(record.levelname, "")
            record.levelname = f"{color}{record.levelname}{self.RESET}"

        # Format the record
        result = super().format(record)

        # Restore original values
        record.levelname = original_levelname
        record.exc_info = exc_info
        record.exc_text = exc_text

        return result


class FullTracebackConsoleFormatter(logging.Formatter):
    """Formatter that includes full tracebacks on console (headless mode or debug mode)."""

    def format(self, record):
        """Format log record with full traceback, no color."""
        # Use default formatting which includes tracebacks
        return super().format(record)


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


def configure_logging(log_file: Path, headless: bool = False) -> Path:
    """
    Configure dual-output logging for YACBA.

    Interactive mode (default):
    - Console: Succinct, colored output (stderr), NO tracebacks
    - File: Complete logs with timestamps and full tracebacks

    Headless mode:
    - Console: Full error output with tracebacks (stderr)
    - File: Complete logs with timestamps and full tracebacks

    Debug mode (YACBA_SHOW_ALL_ERRORS=1):
    - Console: Full error output with tracebacks (even in interactive mode)
    - Shows suppressed errors
    - File: Complete logs with timestamps and full tracebacks

    Args:
        log_file: Path to log file (use utils.session_utils.get_log_path())
        headless: Whether running in headless mode (default: False)

    Returns:
        Path to the log file
    
    Environment Variables:
        PTHN_LOG: Set log levels (e.g., "info" or "error,yacba.config=debug")
        YACBA_SHOW_ALL_ERRORS: If "1", show full tracebacks and suppressed errors on console
    """
    # Initialize envlog for environment-based config
    envlog.init(env_var="PTHN_LOG")
    
    # Check if user wants full error output (debug mode)
    show_all_errors = os.environ.get("YACBA_SHOW_ALL_ERRORS") == "1"

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()

    # Configure console handler (modify existing or create new)
    console_handler = None
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stderr:
            console_handler = handler
            break

    if console_handler:
        # Modify existing console handler based on mode
        if headless or show_all_errors:
            # Headless mode or debug mode: full tracebacks on stderr
            console_handler.setFormatter(
                FullTracebackConsoleFormatter(
                    fmt="%(levelname)s: %(message)s",
                )
            )
        else:
            # Interactive mode: succinct output WITHOUT tracebacks
            console_handler.setFormatter(
                NoTracebackConsoleFormatter("%(levelname)s: %(message)s")
            )
    else:
        # Create console handler if none exists
        console_handler = logging.StreamHandler(sys.stderr)
        if headless or show_all_errors:
            # Headless mode or debug mode: full tracebacks on stderr
            console_handler.setFormatter(
                FullTracebackConsoleFormatter(
                    fmt="%(levelname)s: %(message)s",
                )
            )
        else:
            # Interactive mode: succinct output WITHOUT tracebacks
            console_handler.setFormatter(
                NoTracebackConsoleFormatter("%(levelname)s: %(message)s")
            )
        root_logger.addHandler(console_handler)

    # Add Error Intelligence filter only in interactive mode (when not in debug mode)
    # In headless mode or debug mode, we want raw errors, not enhanced messages
    if not headless and not show_all_errors:
        # Normal interactive mode: enhance error messages
        # Remove existing ErrorIntelligenceFilter if present
        console_handler.filters = [
            f for f in console_handler.filters
            if not isinstance(f, ErrorIntelligenceFilter)
        ]
        # Add Error Intelligence filter to enhance error messages
        error_intelligence_filter = ErrorIntelligenceFilter()
        console_handler.addFilter(error_intelligence_filter)
    else:
        # Remove ErrorIntelligenceFilter in headless mode or debug mode
        # (debug mode users want to see raw errors with full tracebacks)
        console_handler.filters = [
            f for f in console_handler.filters
            if not isinstance(f, ErrorIntelligenceFilter)
        ]

    # Add file handler for complete logs
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root_logger.addHandler(file_handler)

    return log_file


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


def log_exception(logger, context: str, exc: Exception) -> None:
    """
    Log an exception with full traceback to file, and to console based on mode.

    In interactive mode: clean message to console, full traceback to file
    In headless mode: full traceback to console (stderr) and file
    In debug mode (YACBA_SHOW_ALL_ERRORS=1): full traceback to console and file

    Args:
        logger: Logger instance to use
        context: Context string (event name)
        exc: Exception to log
    """
    message = f"{context}: {exc}" if context else str(exc)

    # This will:
    # Interactive mode:
    #   - Print clean message to console: "ERROR: API call failed: Connection timeout"
    #   - Write full traceback to file with timestamp and location
    # Headless mode or debug mode (YACBA_SHOW_ALL_ERRORS=1):
    #   - Print full traceback to stderr
    #   - Write full traceback to file with timestamp and location
    logger.error(message, exc_info=True)
