"""
Basic tests for core.config.argument_definitions module - FINAL FIXED VERSION.
"""

import pytest
import tempfile
from pathlib import Path
from argparse import ArgumentParser, Namespace, ArgumentError
from unittest.mock import patch

from core.config.argument_definitions import (
    FilesSpec,
    _validate_model_string,
    _validate_bool,
    _validate_int,
    _validate_float,
    _validate_file_or_str
)


class TestModelStringValidation:
    """Test _validate_model_string function."""

    def test_validate_model_string_valid_formats(self):
        """Test _validate_model_string with valid model strings."""
        valid_models = [
            'litellm:gemini/gemini-1.5-flash',
            'openai:gpt-4',
            'anthropic:claude-3-sonnet',
        ]
        
        for model in valid_models:
            result = _validate_model_string(model)
            assert result == model
            assert ':' in result

    def test_validate_model_string_shorthand_formats(self):
        """Test _validate_model_string with shorthand formats."""
        result = _validate_model_string('gpt-4')
        assert result == 'openai:gpt-4'
        assert ':' in result

    def test_validate_model_string_invalid_formats(self):
        """Test _validate_model_string with invalid formats."""
        # Empty string
        with pytest.raises(ValueError, match="Model string cannot be empty"):
            _validate_model_string('')
        
        # Invalid formats
        with pytest.raises(ValueError, match="Invalid model string format"):
            _validate_model_string(':')
        
        with pytest.raises(ValueError, match="Invalid model string format"):
            _validate_model_string('framework:')
        
        with pytest.raises(ValueError, match="Invalid model string format"):
            _validate_model_string(':model')


class TestBasicValidationFunctions:
    """Test basic validation functions."""

    def test_validate_bool_valid_values(self):
        """Test _validate_bool with valid values."""
        valid_cases = [
            (True, True),
            (False, False),
            ('true', True),
            ('True', True),
            ('false', False),
            ('False', False),
            ('1', True),
            ('0', False),
            ('yes', True),
            ('no', False),
            (None, False)  # Default for CLI flags
        ]
        
        for input_val, expected in valid_cases:
            result = _validate_bool(input_val)
            assert result == expected, f"Failed for input: {input_val}"

    def test_validate_bool_invalid_values(self):
        """Test _validate_bool with invalid values."""
        invalid_values = ['maybe', 'invalid', '2', '-1']
        
        for invalid_val in invalid_values:
            with pytest.raises(ValueError, match="Cannot convert .* to bool"):
                _validate_bool(invalid_val)

    def test_validate_int_valid_values(self):
        """Test _validate_int with valid values."""
        valid_cases = [(0, 0), (42, 42), (-5, -5), ('100', 100), ('-10', -10)]
        for input_val, expected in valid_cases:
            result = _validate_int(input_val)
            assert result == expected
            assert isinstance(result, int)

    def test_validate_int_invalid_values(self):
        """Test _validate_int with invalid values."""
        invalid_values = ['not_a_number', '3.14', 'abc', '']
        for val in invalid_values:
            with pytest.raises(ValueError, match="Cannot convert .* to int"):
                _validate_int(val)

    def test_validate_float_valid_values(self):
        """Test _validate_float with valid values."""
        valid_cases = [(0.0, 0.0), (3.14, 3.14), (-2.5, -2.5), ('1.5', 1.5), (42, 42.0)]
        for input_val, expected in valid_cases:
            result = _validate_float(input_val)
            assert result == expected
            assert isinstance(result, float)

    def test_validate_float_invalid_values(self):
        """Test _validate_float with invalid values - FIXED."""
        # Only test truly invalid values (inf and nan are actually valid floats!)
        invalid_values = ['not_a_number', 'abc', '']
        for val in invalid_values:
            with pytest.raises(ValueError, match="Cannot convert .* to float"):
                _validate_float(val)

    def test_validate_file_or_str_direct_string(self):
        """Test _validate_file_or_str with direct string input."""
        result = _validate_file_or_str("Direct input")
        assert result == "Direct input"

    def test_validate_file_or_str_file_reference(self):
        """Test _validate_file_or_str with @file reference."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tf:
            tf.write("File content")
            tf.flush()
            
            result = _validate_file_or_str(f"@{tf.name}")
            assert result == "File content"
            
            Path(tf.name).unlink()

    def test_validate_file_or_str_missing_file(self):
        """Test _validate_file_or_str with missing file."""
        with pytest.raises(ValueError, match="File .* does not exist"):
            _validate_file_or_str("@/nonexistent/file.txt")


class TestFilesSpecAction:
    """Test the FilesSpec argparse action."""

    def test_files_spec_basic_functionality(self):
        """Test basic FilesSpec functionality."""
        parser = ArgumentParser()
        namespace = Namespace(files=None)
        action = FilesSpec(None, 'files')
        
        # Single argument
        action(parser, namespace, ['*.txt'], '-f')
        assert namespace.files == [['*.txt']]
        
        # Two arguments
        action(parser, namespace, ['*.py', 'text/x-python'], '-f')
        assert namespace.files == [['*.txt'], ['*.py', 'text/x-python']]

    def test_files_spec_invalid_mimetype(self):
        """Test FilesSpec with invalid mimetype."""
        parser = ArgumentParser()
        namespace = Namespace(files=None)
        action = FilesSpec(None, 'files')
        
        with pytest.raises(ArgumentError, match="expects the second argument to be a mimetype"):
            action(parser, namespace, ['*.txt', 'invalid-mimetype'], '-f')

    def test_files_spec_too_many_arguments(self):
        """Test FilesSpec with too many arguments."""
        parser = ArgumentParser()
        namespace = Namespace(files=None)
        action = FilesSpec(None, 'files')
        
        with pytest.raises(ArgumentError, match="expects up to two arguments"):
            action(parser, namespace, ['*.txt', 'text/plain', 'extra'], '-f')