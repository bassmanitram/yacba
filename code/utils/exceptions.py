"""
Intelligent exception handling and formatting for YACBA.

This module provides smart exception categorization and user-friendly
error messages, reducing noise from expected provider errors while
maintaining full tracebacks for unexpected issues.
"""

import json
import re
from typing import Optional, Tuple
from utils.logging import get_logger

logger = get_logger(__name__)


class ExceptionCategory:
    """Exception categories for different handling strategies."""

    PROVIDER_ERROR = (
        "provider"  # AI provider errors (e.g., rate limits, service unavailable)
    )
    USER_ERROR = "user"  # User-facing errors (e.g., file not found, config errors)
    SYSTEM_ERROR = "system"  # Internal errors (e.g., import errors, bugs)


def categorize_exception(exc: Exception) -> str:
    """
    Categorize an exception based on its type and context.

    Args:
        exc: The exception to categorize

    Returns:
        ExceptionCategory constant
    """
    exc_type = type(exc).__name__
    exc_module = type(exc).__module__

    # Provider errors (litellm, openai, anthropic, etc.)
    provider_patterns = [
        "litellm",
        "openai",
        "anthropic",
        "vertex_ai",
        "RateLimitError",
        "ServiceUnavailableError",
        "APIError",
        "APIConnectionError",
        "Timeout",
    ]

    if any(
        pattern in exc_module or pattern in exc_type for pattern in provider_patterns
    ):
        return ExceptionCategory.PROVIDER_ERROR

    # User errors (file system, configuration, validation)
    user_error_types = [
        "FileNotFoundError",
        "PermissionError",
        "ValueError",
        "ConfigNotFoundError",
        "ProfileNotFoundError",
        "ValidationError",
    ]

    if exc_type in user_error_types:
        return ExceptionCategory.USER_ERROR

    # Everything else is a system error
    return ExceptionCategory.SYSTEM_ERROR


def extract_provider_error_message(exc: Exception) -> Optional[str]:
    """
    Extract a clean error message from provider exceptions.

    Handles various formats:
    - JSON error responses
    - Byte-encoded responses
    - Plain error messages

    Args:
        exc: The exception

    Returns:
        Clean error message or None if extraction fails
    """
    exc_str = str(exc)

    # Try to extract from JSON (common in API errors)
    # Pattern: b'{"error": {"code": 503, "message": "...", "status": "..."}}'
    try:
        # Remove b' prefix and ' suffix if present
        cleaned = exc_str
        if cleaned.startswith("b'") or cleaned.startswith('b"'):
            cleaned = cleaned[2:-1]

        # Try to parse as JSON
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try unescaping newlines first
            cleaned = cleaned.replace("\\n", "\n")
            data = json.loads(cleaned)

        # Extract error details
        if isinstance(data, dict) and "error" in data:
            error = data["error"]
            code = error.get("code", "")
            message = error.get("message", "")
            status = error.get("status", "")

            parts = []
            if message:
                parts.append(message)
            if code:
                parts.append(f"[{code}]")
            if status:
                parts.append(f"[{status}]")

            return " ".join(parts) if parts else None

    except (json.JSONDecodeError, KeyError, AttributeError):
        pass

    # Try to extract from common error message patterns
    # Pattern: "Error: message here"
    match = re.search(r"(?:Error|error):\s*(.+?)(?:\n|$)", exc_str)
    if match:
        return match.group(1).strip()

    # Pattern: status code and message
    match = re.search(r"(\d{3})\s+(.+?)(?:\n|$)", exc_str)
    if match:
        return f"{match.group(2)} [{match.group(1)}]"

    # Return first line if short enough
    first_line = exc_str.split("\n")[0]
    if len(first_line) <= 200:
        return first_line

    return None


def format_exception(exc: Exception) -> Tuple[str, bool]:
    """
    Format an exception for user display.

    Args:
        exc: The exception to format

    Returns:
        Tuple of (formatted_message, should_show_traceback)
    """
    import os

    category = categorize_exception(exc)
    exc_type = type(exc).__name__

    # Check if user has explicitly requested all tracebacks
    force_all_tracebacks = os.environ.get("YACBA_LOG_TRACEBACKS", "").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

    if category == ExceptionCategory.PROVIDER_ERROR:
        # Extract clean message from provider errors
        clean_msg = extract_provider_error_message(exc)

        if clean_msg:
            # Determine provider from exception type
            provider = "Unknown"
            if (
                "vertex" in exc_type.lower()
                or "vertexai" in str(type(exc).__module__).lower()
            ):
                provider = "VertexAI/Gemini"
            elif "openai" in exc_type.lower():
                provider = "OpenAI"
            elif "anthropic" in exc_type.lower():
                provider = "Anthropic"
            elif "litellm" in str(type(exc).__module__).lower():
                provider = "LiteLLM"

            formatted = f"Model Error ({provider}): {clean_msg}"
        else:
            # Fallback to exception type and message
            formatted = f"Model Error ({exc_type}): {str(exc)}"

        # Only show traceback if explicitly forced via env var
        return formatted, force_all_tracebacks

    elif category == ExceptionCategory.USER_ERROR:
        # User errors: clear message, no traceback unless forced
        formatted = f"{exc_type}: {str(exc)}"
        return formatted, force_all_tracebacks

    else:
        # System errors: show full details with traceback
        formatted = f"System Error ({exc_type}): {str(exc)}"
        return formatted, True  # Always show traceback for system errors


def log_exception(logger_instance, event: str, exc: Exception, **kwargs) -> None:
    """
    Log an exception with intelligent formatting.

    This is the recommended way to log exceptions in YACBA. It automatically
    categorizes the exception and formats it appropriately.

    Args:
        logger_instance: The logger to use
        event: Event name (e.g., "model_request_failed")
        exc: The exception to log
        **kwargs: Additional context

    Example:
        try:
            await model.generate(prompt)
        except Exception as e:
            log_exception(logger, "generation_failed", e, prompt_length=len(prompt))
    """
    formatted_msg, should_trace = format_exception(exc)

    # Add formatted message to context
    kwargs["error"] = formatted_msg
    kwargs["error_type"] = type(exc).__name__

    # Log with or without traceback
    if should_trace:
        kwargs["exc_info"] = True

    logger_instance.error(event, **kwargs)
