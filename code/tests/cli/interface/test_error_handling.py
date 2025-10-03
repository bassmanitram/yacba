"""
Tests for cli.interface.error_handling module.

Comprehensive testing of error formatting and exception handling utilities.
"""

import pytest
from requests import Response
from unittest.mock import Mock

from utils.error_handling import format_error


class TestFormatError:
    """Test error formatting functionality."""

    def test_format_error_basic_exception(self):
        """Test basic exception formatting."""
        exc = ValueError("Basic error message")
        result = format_error(exc)
        assert result == "Basic error message"

    def test_format_error_with_message_attribute(self):
        """Test exception with custom message attribute."""
        exc = Exception("Standard message")
        exc.message = "Custom message attribute"
        
        result = format_error(exc)
        # Should still return the standard string representation
        assert result == "Standard message"

    def test_format_error_with_response_attribute(self):
        """Test exception with response attribute (API errors)."""
        exc = Exception("API error")
        
        # Mock response object
        mock_response = Mock()
        mock_response.text = "Detailed API error response"
        exc.response = mock_response
        
        result = format_error(exc)
        assert result == "API error"

    def test_format_error_with_both_message_and_response(self):
        """Test exception with both message and response attributes."""
        exc = Exception("Main error")
        exc.message = "Custom message"
        
        mock_response = Mock()
        mock_response.text = "API response details"
        exc.response = mock_response
        
        result = format_error(exc)
        assert result == "Main error"

    def test_format_error_response_without_text(self):
        """Test exception with response that has no text attribute."""
        exc = Exception("Error with response")
        exc.response = Mock(spec=[])  # Mock without text attribute
        
        result = format_error(exc)
        assert result == "Error with response"

    def test_format_error_custom_exception_types(self):
        """Test formatting various exception types."""
        exceptions = [
            ValueError("Value error"),
            TypeError("Type error"), 
            KeyError("key_error"),
            AttributeError("Attribute error"),
            ImportError("Import error")
        ]
        
        for exc in exceptions:
            result = format_error(exc)
            assert result == str(exc)

    def test_format_error_empty_message(self):
        """Test exception with empty message."""
        exc = Exception("")
        result = format_error(exc)
        assert result == ""

    def test_format_error_none_message_attribute(self):
        """Test exception where message attribute is None."""
        exc = Exception("Main message")
        exc.message = None
        
        result = format_error(exc)
        assert result == "Main message"