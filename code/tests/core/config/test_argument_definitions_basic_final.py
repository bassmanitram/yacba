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


class TestUICustomizationArguments:
    """Test UI customization argument definitions."""

    def test_cli_prompt_argument_definition_exists(self):
        """Test that --cli-prompt argument is properly defined."""
        from core.config.argument_definitions import ARGUMENT_DEFINITIONS
        
        cli_prompt_arg = None
        for arg_def in ARGUMENT_DEFINITIONS:
            if arg_def.argname == 'cli_prompt':
                cli_prompt_arg = arg_def
                break
        
        assert cli_prompt_arg is not None, "--cli-prompt argument not found in definitions"
        assert '--cli-prompt' in cli_prompt_arg.names
        assert arg_def.argname == 'cli_prompt'
        assert 'HTML formatting' in arg_def.help
        assert 'skyblue' in arg_def.help  # Check example is included

    def test_response_prefix_argument_definition_exists(self):
        """Test that --response-prefix argument is properly defined."""
        from core.config.argument_definitions import ARGUMENT_DEFINITIONS
        
        response_prefix_arg = None
        for arg_def in ARGUMENT_DEFINITIONS:
            if arg_def.argname == 'response_prefix':
                response_prefix_arg = arg_def
                break
        
        assert response_prefix_arg is not None, "--response-prefix argument not found in definitions"
        assert '--response-prefix' in response_prefix_arg.names
        assert arg_def.argname == 'response_prefix'
        assert 'HTML formatting' in arg_def.help
        assert 'seagreen' in arg_def.help  # Check example is included

    def test_ui_arguments_in_parser(self):
        """Test that UI customization arguments are included in argument parser."""
        from core.config.argument_definitions import parse_args
        from unittest.mock import patch
        import sys
        
        # Test parsing with UI arguments
        test_argv = [
            'yacba',
            '--model', 'gpt-4',
            '--system-prompt', 'Test',
            '--cli-prompt', '<b><blue>You: </blue></b>',
            '--response-prefix', '<b><green>Bot: </green></b>'
        ]
        
        with patch.object(sys, 'argv', test_argv):
            args = parse_args()
            assert hasattr(args, 'cli_prompt')
            assert hasattr(args, 'response_prefix')
            assert args.cli_prompt == '<b><blue>You: </blue></b>'
            assert args.response_prefix == '<b><green>Bot: </green></b>'

    def test_ui_arguments_optional(self):
        """Test that UI customization arguments are optional."""
        from core.config.argument_definitions import parse_args
        from unittest.mock import patch
        import sys
        
        # Test parsing without UI arguments
        test_argv = [
            'yacba',
            '--model', 'gpt-4',
            '--system-prompt', 'Test'
        ]
        
        with patch.object(sys, 'argv', test_argv):
            args = parse_args()
            assert hasattr(args, 'cli_prompt')
            assert hasattr(args, 'response_prefix')
            assert args.cli_prompt is None
            assert args.response_prefix is None

    def test_ui_arguments_with_html_formatting(self):
        """Test UI arguments with complex HTML formatting."""
        from core.config.argument_definitions import parse_args
        from unittest.mock import patch
        import sys
        
        complex_cli_prompt = '<b style="color: #4A90E2"><span>👤 You:</span></b> '
        complex_response_prefix = '<div class="bot-response"><b><span style="color: #50C878">🤖 Assistant:</span></b></div>'
        
        test_argv = [
            'yacba',
            '--model', 'gpt-4',
            '--system-prompt', 'Test',
            '--cli-prompt', complex_cli_prompt,
            '--response-prefix', complex_response_prefix
        ]
        
        with patch.object(sys, 'argv', test_argv):
            args = parse_args()
            assert args.cli_prompt == complex_cli_prompt
            assert args.response_prefix == complex_response_prefix

    def test_ui_arguments_validation_none_required(self):
        """Test that UI arguments don't require special validation."""
        from core.config.argument_definitions import validate_args
        
        # Test config with UI arguments
        config = {
            'model': 'gpt-4',
            'system_prompt': 'Test',
            'cli_prompt': '<b>Custom prompt:</b>',
            'response_prefix': '<i>Response:</i>'
        }
        
        # Should not raise any validation errors
        validated_config = validate_args(config)
        assert validated_config['cli_prompt'] == '<b>Custom prompt:</b>'
        assert validated_config['response_prefix'] == '<i>Response:</i>'

    def test_ui_arguments_empty_strings_allowed(self):
        """Test that empty strings are allowed for UI arguments."""
        from core.config.argument_definitions import validate_args
        
        config = {
            'model': 'gpt-4',
            'system_prompt': 'Test',
            'cli_prompt': '',
            'response_prefix': ''
        }
        
        validated_config = validate_args(config)
        assert validated_config['cli_prompt'] == ''
        assert validated_config['response_prefix'] == ''
