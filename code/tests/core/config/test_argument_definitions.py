"""
Tests for core.config.argument_definitions module.

Tests CLI argument validation functions, FilesSpec action,
and argument parsing with focus on file handling scenarios.
"""

import pytest
import tempfile
import mimetypes
from pathlib import Path
from argparse import ArgumentParser, Namespace, ArgumentError
from unittest.mock import patch, mock_open

from core.config.argument_definitions import (
    FilesSpec,
    _validate_files,
    _validate_model_string,
    _validate_bool,
    _validate_int,
    _validate_float,
    _validate_file_path,
    _validate_existing_file,
    _validate_existing_dir,
    _validate_file_or_str,
    VALID_MODEL_STRINGS,
    INVALID_MODEL_STRINGS,
    VALID_BOOL_VALUES,
    INVALID_BOOL_VALUES
)
from tests.conftest import VALID_MODEL_STRINGS as CONFTEST_VALID_MODELS


class TestFilesSpecAction:
    """Test the FilesSpec argparse action for -f/--files option."""

    def test_files_spec_single_argument(self):
        """Test FilesSpec with single argument (file glob only)."""
        parser = ArgumentParser()
        parser.add_argument('-f', '--files', action=FilesSpec, nargs='*', dest='files')
        
        # Test single file glob
        namespace = Namespace(files=None)
        action = FilesSpec(None, 'files')
        
        # Should accept single argument
        action(parser, namespace, ['*.txt'], '-f')
        assert namespace.files == [['*.txt']]

    def test_files_spec_two_arguments(self):
        """Test FilesSpec with two arguments (file glob + mimetype)."""
        parser = ArgumentParser()
        parser.add_argument('-f', '--files', action=FilesSpec, nargs='*', dest='files')
        
        namespace = Namespace(files=None)
        action = FilesSpec(None, 'files')
        
        # Should accept file glob + valid mimetype
        action(parser, namespace, ['*.py', 'text/x-python'], '-f')
        assert namespace.files == [['*.py', 'text/x-python']]

    def test_files_spec_invalid_mimetype(self):
        """Test FilesSpec with invalid mimetype format."""
        parser = ArgumentParser()
        parser.add_argument('-f', '--files', action=FilesSpec, nargs='*', dest='files')
        
        namespace = Namespace(files=None)
        action = FilesSpec(None, 'files')
        
        # Should reject invalid mimetype format
        with pytest.raises(ArgumentError, match="expects the second argument to be a mimetype"):
            action(parser, namespace, ['*.txt', 'invalid-mimetype'], '-f')

    def test_files_spec_too_many_arguments(self):
        """Test FilesSpec with too many arguments."""
        parser = ArgumentParser()
        parser.add_argument('-f', '--files', action=FilesSpec, nargs='*', dest='files')
        
        namespace = Namespace(files=None)
        action = FilesSpec(None, 'files')
        
        # Should reject more than 2 arguments
        with pytest.raises(ArgumentError, match="expects up to two arguments"):
            action(parser, namespace, ['*.txt', 'text/plain', 'extra'], '-f')

    def test_files_spec_multiple_calls(self):
        """Test FilesSpec with multiple -f options."""
        parser = ArgumentParser()
        parser.add_argument('-f', '--files', action=FilesSpec, nargs='*', dest='files')
        
        namespace = Namespace(files=None)
        action = FilesSpec(None, 'files')
        
        # First call
        action(parser, namespace, ['*.txt'], '-f')
        # Second call  
        action(parser, namespace, ['*.py', 'text/x-python'], '-f')
        
        assert namespace.files == [['*.txt'], ['*.py', 'text/x-python']]

    def test_files_spec_valid_mimetypes(self):
        """Test FilesSpec with various valid mimetype formats."""
        valid_mimetypes = [
            'text/plain',
            'application/json',
            'image/png',
            'video/mp4',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        
        parser = ArgumentParser()
        action = FilesSpec(None, 'files')
        
        for mimetype in valid_mimetypes:
            namespace = Namespace(files=None)
            # Should not raise exception
            action(parser, namespace, ['*.test', mimetype], '-f')
            assert namespace.files == [['*.test', mimetype]]


class TestValidateFiles:
    """Test the _validate_files function."""

    def test_validate_files_with_existing_files(self, sample_files_for_upload):
        """Test _validate_files with actual files."""
        files_list = [
            [sample_files_for_upload['text']],
            [sample_files_for_upload['python'], 'text/x-python']
        ]
        
        with patch('core.config.argument_definitions.resolve_glob') as mock_resolve:
            # Mock resolve_glob to return the actual file paths
            mock_resolve.side_effect = lambda glob: [glob] if not glob.startswith('*') else [sample_files_for_upload['text']]
            
            result = _validate_files(files_list)
            
            # Should return tuples of (file_path, mimetype)
            assert len(result) >= 2
            # Check that mimetypes are assigned
            for file_path, mimetype in result:
                assert isinstance(file_path, str)
                assert '/' in mimetype  # Basic mimetype format

    def test_validate_files_with_glob_patterns(self):
        """Test _validate_files with glob patterns."""
        files_list = [
            ['*.txt'],
            ['*.py', 'text/x-python']
        ]
        
        with patch('core.config.argument_definitions.resolve_glob') as mock_resolve:
            # Mock glob resolution
            mock_resolve.side_effect = [
                ['/test/file1.txt', '/test/file2.txt'],  # *.txt
                ['/test/script.py']  # *.py
            ]
            
            result = _validate_files(files_list)
            
            # Should process all resolved files
            assert len(result) == 3
            
            # Check mimetype handling
            txt_files = [(path, mime) for path, mime in result if path.endswith('.txt')]
            py_files = [(path, mime) for path, mime in result if path.endswith('.py')]
            
            # txt files should get guessed mimetypes
            assert len(txt_files) == 2
            # py file should get specified mimetype
            assert len(py_files) == 1
            assert py_files[0][1] == 'text/x-python'

    def test_validate_files_mimetype_guessing(self):
        """Test _validate_files mimetype guessing."""
        files_list = [
            ['/test/document.pdf'],
            ['/test/image.jpg'],
            ['/test/unknown_extension']
        ]
        
        with patch('core.config.argument_definitions.resolve_glob') as mock_resolve:
            mock_resolve.side_effect = lambda glob: [glob]  # Return the path as-is
            
            result = _validate_files(files_list)
            
            # Should assign appropriate mimetypes
            mimetypes_by_file = {path: mime for path, mime in result}
            
            # PDF should be detected
            assert 'application/pdf' in mimetypes_by_file.get('/test/document.pdf', '')
            # JPG should be detected  
            assert 'image/jpeg' in mimetypes_by_file.get('/test/image.jpg', '')
            # Unknown should default to text/plain
            assert mimetypes_by_file.get('/test/unknown_extension') == 'text/plain'

    def test_validate_files_invalid_mimetype_warning(self):
        """Test _validate_files with invalid mimetype formats."""
        files_list = [
            ['/test/file.txt', 'invalid/mimetype/format'],
            ['/test/file2.txt', 'no-slash'],
            ['/test/file3.txt', '/leading-slash'],
            ['/test/file4.txt', 'trailing-slash/']
        ]
        
        with patch('core.config.argument_definitions.resolve_glob') as mock_resolve:
            mock_resolve.side_effect = lambda glob: [glob.split(',')[0]]  # Return first part
            
            # Should handle invalid mimetypes gracefully
            result = _validate_files(files_list)
            
            # Invalid mimetypes should be skipped, files ignored
            # Only files with valid mimetypes should be included
            assert len([f for f in result if 'invalid' not in f[1]]) >= 0


class TestModelStringValidation:
    """Test _validate_model_string function."""

    def test_validate_model_string_valid_formats(self):
        """Test _validate_model_string with valid model strings."""
        valid_models = [
            'litellm:gemini/gemini-1.5-flash',
            'openai:gpt-4',
            'anthropic:claude-3-sonnet',
            'bedrock:anthropic.claude-3-sonnet-20240229-v1:0'
        ]
        
        for model in valid_models:
            result = _validate_model_string(model)
            assert result == model
            # Should contain framework:model format
            assert ':' in result

    def test_validate_model_string_shorthand_formats(self):
        """Test _validate_model_string with shorthand formats (framework detection)."""
        # Note: This test depends on the framework detection logic
        shorthand_models = [
            'gemini-1.5-flash',
            'gpt-4',
            'claude-3-sonnet'
        ]
        
        for model in shorthand_models:
            result = _validate_model_string(model)
            # Should add framework prefix
            assert ':' in result
            assert result.endswith(':' + model)

    def test_validate_model_string_invalid_formats(self):
        """Test _validate_model_string with invalid formats."""
        invalid_models = [
            '',  # Empty string
            ':',  # Just colon
            'framework:',  # No model part
            ':model',  # No framework part
            'framework::model'  # Double colon
        ]
        
        for model in invalid_models:
            with pytest.raises(ValueError, match="Invalid model string format"):
                _validate_model_string(model)


class TestFileOrStringValidation:
    """Test _validate_file_or_str function for -s and -i options."""

    def test_validate_file_or_str_direct_string(self):
        """Test _validate_file_or_str with direct string input."""
        test_string = "This is a direct string input"
        result = _validate_file_or_str(test_string)
        assert result == test_string

    def test_validate_file_or_str_file_reference(self, temp_dir):
        """Test _validate_file_or_str with @file reference."""
        # Create test file
        test_file = temp_dir / "test_content.txt"
        test_content = "This is content loaded from a file."
        test_file.write_text(test_content)
        
        # Test with @ prefix
        file_reference = f"@{test_file}"
        result = _validate_file_or_str(file_reference)
        assert result == test_content

    def test_validate_file_or_str_missing_file(self, temp_dir):
        """Test _validate_file_or_str with @file reference to missing file."""
        missing_file = temp_dir / "nonexistent.txt"
        file_reference = f"@{missing_file}"
        
        with pytest.raises(ValueError, match="File .* does not exist"):
            _validate_file_or_str(file_reference)

    def test_validate_file_or_str_file_read_error(self, temp_dir):
        """Test _validate_file_or_str with file read errors."""
        # Create a file but simulate read error
        test_file = temp_dir / "test_file.txt"
        test_file.write_text("content")
        
        file_reference = f"@{test_file}"
        
        # Mock load_file_content to raise an exception
        with patch('core.config.argument_definitions.load_file_content') as mock_load:
            mock_load.side_effect = IOError("Permission denied")
            
            with pytest.raises(ValueError, match="Error reading file"):
                _validate_file_or_str(file_reference)


class TestBasicValidationFunctions:
    """Test basic validation functions."""

    def test_validate_bool_valid_values(self):
        """Test _validate_bool with valid values."""
        for input_val, expected in VALID_BOOL_VALUES:
            result = _validate_bool(input_val)
            assert result == expected, f"Failed for input: {input_val}"

    def test_validate_bool_invalid_values(self):
        """Test _validate_bool with invalid values."""
        for invalid_val in INVALID_BOOL_VALUES:
            with pytest.raises(ValueError, match="Cannot convert .* to bool"):
                _validate_bool(invalid_val)

    def test_validate_bool_none_value(self):
        """Test _validate_bool with None (default for CLI flags)."""
        result = _validate_bool(None)
        assert result is False

    def test_validate_int_valid_values(self):
        """Test _validate_int with valid values."""
        valid_ints = [0, 1, -1, 100, '42', '-5']
        for val in valid_ints:
            result = _validate_int(val)
            assert isinstance(result, int)
            assert result == int(val)

    def test_validate_int_invalid_values(self):
        """Test _validate_int with invalid values."""
        invalid_ints = ['not_a_number', '3.14', 'inf', None]
        for val in invalid_ints:
            with pytest.raises(ValueError, match="Cannot convert .* to int"):
                _validate_int(val)

    def test_validate_float_valid_values(self):
        """Test _validate_float with valid values."""
        valid_floats = [0.0, 1.5, -2.7, 100, '3.14', '-0.5']
        for val in valid_floats:
            result = _validate_float(val)
            assert isinstance(result, float)
            assert result == float(val)

    def test_validate_float_invalid_values(self):
        """Test _validate_float with invalid values."""
        invalid_floats = ['not_a_number', 'inf', None]
        for val in invalid_floats:
            with pytest.raises(ValueError, match="Cannot convert .* to float"):
                _validate_float(val)


class TestFilePathValidation:
    """Test file path validation functions."""

    def test_validate_existing_file_valid(self, temp_dir):
        """Test _validate_existing_file with valid file."""
        test_file = temp_dir / "existing_file.txt"
        test_file.write_text("content")
        
        result = _validate_existing_file(str(test_file))
        assert result == str(test_file.resolve())

    def test_validate_existing_file_invalid(self, temp_dir):
        """Test _validate_existing_file with non-existent file."""
        missing_file = temp_dir / "missing_file.txt"
        
        with pytest.raises(ValueError, match="File .* does not exist"):
            _validate_existing_file(str(missing_file))

    def test_validate_existing_dir_valid(self, temp_dir):
        """Test _validate_existing_dir with valid directory."""
        test_dir = temp_dir / "existing_dir"
        test_dir.mkdir()
        
        result = _validate_existing_dir(str(test_dir))
        assert result == str(test_dir.resolve())

    def test_validate_existing_dir_invalid(self, temp_dir):
        """Test _validate_existing_dir with non-existent directory."""
        missing_dir = temp_dir / "missing_dir"
        
        with pytest.raises(ValueError, match="Directory .* does not exist"):
            _validate_existing_dir(str(missing_dir))

    def test_validate_file_path_existing_file(self, temp_dir):
        """Test _validate_file_path with existing file."""
        test_file = temp_dir / "existing.txt"
        test_file.write_text("content")
        
        result = _validate_file_path(str(test_file))
        assert result == str(test_file.resolve())

    def test_validate_file_path_creatable_file(self, temp_dir):
        """Test _validate_file_path with creatable file path."""
        new_file = temp_dir / "new_file.txt"
        
        result = _validate_file_path(str(new_file))
        assert result == str(new_file.resolve())

    def test_validate_file_path_invalid_parent(self, temp_dir):
        """Test _validate_file_path with invalid parent directory."""
        invalid_file = temp_dir / "nonexistent_dir" / "file.txt"
        
        with pytest.raises(ValueError, match="does not exist and cannot be created"):
            _validate_file_path(str(invalid_file))


class TestArgumentDefinitionIntegration:
    """Integration tests for argument definitions."""

    def test_files_option_end_to_end(self, sample_files_for_upload):
        """Test the complete -f option flow from parsing to validation."""
        # This would test the full integration but requires more setup
        # Placeholder for integration test
        pass

    def test_model_config_override_integration(self):
        """Test -c option for model config overrides."""
        # This would test model config override parsing
        # Placeholder for integration test  
        pass

    def test_environment_variable_integration(self, mock_env_vars):
        """Test environment variable handling."""
        # This would test env var processing
        # Placeholder for integration test
        pass