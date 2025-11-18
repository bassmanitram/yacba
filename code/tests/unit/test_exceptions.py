"""
Unit tests for exception handling utilities.
"""

from utils.exceptions import (
    categorize_exception,
    extract_provider_error_message,
    format_exception,
    ExceptionCategory,
)


class MockVertexAIError(Exception):
    """Mock VertexAI exception for testing."""

    __module__ = "litellm.llms.vertex_ai.common_utils"
    pass


class MockOpenAIError(Exception):
    """Mock OpenAI exception for testing."""

    __module__ = "openai.error"
    pass


def test_categorize_provider_errors():
    """Test that provider errors are correctly categorized."""
    # VertexAI error
    exc = MockVertexAIError("test error")
    assert categorize_exception(exc) == ExceptionCategory.PROVIDER_ERROR

    # OpenAI error
    exc = MockOpenAIError("test error")
    assert categorize_exception(exc) == ExceptionCategory.PROVIDER_ERROR


def test_categorize_user_errors():
    """Test that user errors are correctly categorized."""
    exc = FileNotFoundError("config.yaml not found")
    assert categorize_exception(exc) == ExceptionCategory.USER_ERROR

    exc = PermissionError("Cannot write to directory")
    assert categorize_exception(exc) == ExceptionCategory.USER_ERROR

    exc = ValueError("Invalid configuration value")
    assert categorize_exception(exc) == ExceptionCategory.USER_ERROR


def test_categorize_system_errors():
    """Test that system errors are correctly categorized."""
    exc = ImportError("Module not found")
    assert categorize_exception(exc) == ExceptionCategory.SYSTEM_ERROR

    exc = AttributeError("Object has no attribute")
    assert categorize_exception(exc) == ExceptionCategory.SYSTEM_ERROR


def test_extract_json_error_message():
    """Test extraction from JSON-formatted error."""
    error_msg = b'{"error": {"code": 503, "message": "Service overloaded", "status": "UNAVAILABLE"}}'
    exc = MockVertexAIError(error_msg)

    result = extract_provider_error_message(exc)
    assert result == "Service overloaded [503] [UNAVAILABLE]"


def test_extract_json_error_with_newlines():
    """Test extraction from JSON with escaped newlines."""
    error_msg = b'{\\n  "error": {\\n    "code": 503,\\n    "message": "The model is overloaded. Please try again later.",\\n    "status": "UNAVAILABLE"\\n  }\\n}\\n'
    exc = MockVertexAIError(error_msg)

    result = extract_provider_error_message(exc)
    assert "The model is overloaded" in result
    assert "503" in result
    assert "UNAVAILABLE" in result


def test_extract_plain_error_message():
    """Test extraction from plain error message."""
    exc = Exception("Error: Connection timeout")
    result = extract_provider_error_message(exc)
    assert result == "Connection timeout"


def test_format_provider_error():
    """Test formatting of provider errors."""
    error_msg = b'{"error": {"code": 503, "message": "Service overloaded", "status": "UNAVAILABLE"}}'
    exc = MockVertexAIError(error_msg)

    formatted, should_trace = format_exception(exc)

    assert "Model Error" in formatted
    assert "Service overloaded" in formatted
    assert should_trace is False  # Provider errors don't show traceback by default


def test_format_user_error():
    """Test formatting of user errors."""
    exc = FileNotFoundError("config.yaml not found")

    formatted, should_trace = format_exception(exc)

    assert "FileNotFoundError" in formatted
    assert "config.yaml not found" in formatted
    assert should_trace is False  # User errors don't show traceback by default


def test_format_system_error():
    """Test formatting of system errors."""
    exc = ImportError("No module named 'xyz'")

    formatted, should_trace = format_exception(exc)

    assert "System Error" in formatted
    assert "ImportError" in formatted
    assert should_trace is True  # System errors always show traceback


def test_provider_detection_vertex():
    """Test provider detection for VertexAI/Gemini."""
    error_msg = b'{"error": {"message": "Test error"}}'
    exc = MockVertexAIError(error_msg)

    formatted, _ = format_exception(exc)

    assert "VertexAI/Gemini" in formatted


def test_provider_detection_openai():
    """Test provider detection for OpenAI."""
    exc = MockOpenAIError("Rate limit exceeded")

    formatted, _ = format_exception(exc)

    assert "OpenAI" in formatted


def test_extract_without_json():
    """Test extraction when error is not JSON."""
    exc = Exception("Simple error message")
    result = extract_provider_error_message(exc)
    assert result == "Simple error message"


def test_extract_multiline_first_line():
    """Test extraction takes first line for multi-line errors."""
    exc = Exception("First line error\nSecond line\nThird line")
    result = extract_provider_error_message(exc)
    assert result == "First line error"


def test_format_with_very_long_message():
    """Test handling of very long error messages."""
    long_msg = "x" * 500
    exc = Exception(long_msg)

    formatted, _ = format_exception(exc)

    # Should still work, just might truncate
    assert "System Error" in formatted
