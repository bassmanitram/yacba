"""
Centralized logging configuration for YACBA using structlog.

This module provides a unified logging interface that supports:
- Per-module logger hierarchies
- Structured logging with context
- Configurable output formats (console, JSON)
- Integration with Python's stdlib logging
- Easy per-module level control
- Configurable exception tracebacks

Usage:
    from utils.logging import get_logger, log_error
    
    logger = get_logger(__name__)
    logger.info("operation_completed", item_count=42, duration_ms=123)
    
    # Error logging with automatic traceback handling
    try:
        risky_operation()
    except Exception as e:
        log_error(logger, "operation_failed", error=str(e))
"""

import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import Optional, Any

import structlog


# Module-level configuration
_configured = False
_default_level = logging.INFO
_include_tracebacks = True


def configure_logging(
    level: Optional[str] = None,
    json_output: bool = False,
    config_file: Optional[Path] = None,
    include_tracebacks: bool = True
) -> None:
    """
    Configure structlog with sensible defaults.
    
    This should be called once at application startup. Subsequent calls
    are no-ops.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: If True, output JSON instead of console format
        config_file: Optional path to logging config file (YAML or INI)
        include_tracebacks: If True, include stack traces in error logs (default: True)
    """
    global _configured, _default_level, _include_tracebacks
    
    if _configured:
        return
    
    # Check environment variable for traceback control
    env_tracebacks = os.environ.get('YACBA_LOG_TRACEBACKS', '').lower()
    if env_tracebacks in ('0', 'false', 'no', 'off'):
        _include_tracebacks = False
    else:
        _include_tracebacks = include_tracebacks
    
    # Determine log level
    if level:
        _default_level = getattr(logging, level.upper(), logging.INFO)
    elif os.environ.get('YACBA_LOG_LEVEL'):
        _default_level = getattr(logging, os.environ['YACBA_LOG_LEVEL'].upper(), logging.INFO)
    else:
        _default_level = logging.INFO
    
    # Configure stdlib logging first
    if config_file and config_file.exists():
        # Load from config file if provided
        if config_file.suffix in ['.yaml', '.yml']:
            import yaml
            with open(config_file) as f:
                config_dict = yaml.safe_load(f)
                logging.config.dictConfig(config_dict)
        elif config_file.suffix == '.ini':
            logging.config.fileConfig(config_file)
    else:
        # Use basic configuration
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=_default_level,
        )
    
    # Configure per-module levels from environment
    _configure_module_levels()
    
    # Build processor chain
    processors = [
        # Add timestamp
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        # Stack info for errors
        structlog.processors.StackInfoRenderer(),
        # Exception formatting
        structlog.processors.format_exc_info,
        # Unicode handling
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Choose renderer based on output format
    if json_output or os.environ.get('YACBA_LOG_JSON', '').lower() in ('1', 'true', 'yes'):
        # Production: JSON output
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Development: Colored console output
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=sys.stdout.isatty(),  # Only color if outputting to terminal
                exception_formatter=structlog.dev.plain_traceback
            )
        )
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    _configured = True


def _configure_module_levels() -> None:
    """Configure per-module log levels from environment variables."""
    # Check for module-specific environment variables
    # Format: YACBA_LOG_<MODULE>_LEVEL=DEBUG
    for key, value in os.environ.items():
        if key.startswith('YACBA_LOG_') and key.endswith('_LEVEL'):
            # Extract module name: YACBA_LOG_CONFIG_LEVEL -> yacba.config
            module_part = key[10:-6]  # Strip YACBA_LOG_ and _LEVEL
            module_name = f"yacba.{module_part.lower()}"
            
            level = getattr(logging, value.upper(), None)
            if level:
                logging.getLogger(module_name).setLevel(level)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a logger instance for the given name.
    
    This is the primary interface for getting loggers in YACBA.
    Pass __name__ to get a logger with the module's hierarchy.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured structlog logger
        
    Example:
        logger = get_logger(__name__)
        logger.info("user_login", user_id=123, session="abc")
    """
    # Ensure logging is configured
    if not _configured:
        configure_logging()
    
    return structlog.get_logger(name)


def set_module_level(module: str, level: str) -> None:
    """
    Set the logging level for a specific module at runtime.
    
    Args:
        module: Module name (e.g., "yacba.config" or "yacba.adapters.repl_toolkit")
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Example:
        set_module_level("yacba.config", "DEBUG")
        set_module_level("yacba.adapters", "WARNING")
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger(module).setLevel(log_level)


def get_module_level(module: str) -> str:
    """
    Get the current logging level for a module.
    
    Args:
        module: Module name
        
    Returns:
        Level name (e.g., "DEBUG", "INFO")
    """
    logger = logging.getLogger(module)
    return logging.getLevelName(logger.getEffectiveLevel())


def should_include_traceback() -> bool:
    """
    Check if tracebacks should be included in error logs.
    
    Returns:
        bool: True if tracebacks should be included
        
    Example:
        if should_include_traceback():
            logger.error("error", error=str(e), exc_info=True)
        else:
            logger.error("error", error=str(e))
    """
    return _include_tracebacks


def log_error(logger: structlog.stdlib.BoundLogger, event: str, **kwargs: Any) -> None:
    """
    Log an error with conditional traceback inclusion.
    
    This is the recommended way to log errors in YACBA. It automatically
    includes stack traces based on the global configuration.
    
    Args:
        logger: The logger instance
        event: Event name (e.g., "operation_failed")
        **kwargs: Additional context (error=str(e), operation="parse", etc.)
        
    Example:
        logger = get_logger(__name__)
        try:
            risky_operation()
        except Exception as e:
            log_error(logger, "operation_failed", 
                     operation="parse_config",
                     error=str(e))
    """
    if _include_tracebacks:
        kwargs['exc_info'] = True
    logger.error(event, **kwargs)


def set_traceback_mode(enabled: bool) -> None:
    """
    Enable or disable traceback inclusion at runtime.
    
    Args:
        enabled: If True, include tracebacks in error logs
        
    Example:
        from utils.logging import set_traceback_mode
        
        # Disable tracebacks for cleaner output
        set_traceback_mode(False)
        
        # Re-enable for debugging
        set_traceback_mode(True)
    """
    global _include_tracebacks
    _include_tracebacks = enabled


# Pre-configure on import with sensible defaults
# This ensures logging works even if configure_logging() is never called
configure_logging()
