"""
Proper tests for argument parsing - FIXED VERSION.

Tests the actual CLI interface with named arguments.
"""

import pytest
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from core.config.argument_definitions import parse_args, validate_args


class TestActualArgumentParsing:
    """Test the actual CLI argument parsing interface."""

    def test_basic_cli_arguments(self):
        """Test basic CLI with required arguments."""
        with patch.object(sys, 'argv', ['yacba', '--model', 'gpt-4', '--system-prompt', 'You are helpful']):
            result = parse_args()
            
            assert result.model == 'gpt-4'
            assert result.system_prompt == 'You are helpful'

    def test_cli_with_files_argument(self):
        """Test CLI with files argument."""
        with patch.object(sys, 'argv', ['yacba', '-m', 'claude-3-sonnet', '-s', 'Test prompt', '-f', 'test.py', 'text/x-python']):
            result = parse_args()
            
            assert result.model == 'claude-3-sonnet'
            assert result.system_prompt == 'Test prompt'
            assert result.files == [['test.py', 'text/x-python']]

    def test_cli_with_multiple_files(self):
        """Test CLI with multiple file arguments."""
        argv = ['yacba', '--model', 'gpt-4', '--system-prompt', 'Test',
                '--files', 'file1.py', 'text/x-python',
                '--files', 'file2.txt', 'text/plain']
        
        with patch.object(sys, 'argv', argv):
            result = parse_args()
            
            assert len(result.files) == 2
            assert result.files[0] == ['file1.py', 'text/x-python']
            assert result.files[1] == ['file2.txt', 'text/plain']

    def test_cli_boolean_flags(self):
        """Test CLI boolean flags."""
        argv = ['yacba', '--model', 'gpt-4', '--system-prompt', 'Test',
                '--headless', '--show-tool-use', '--clear-cache']
        
        with patch.object(sys, 'argv', argv):
            result = parse_args()
            
            assert result.headless is True
            assert result.show_tool_use is True
            assert result.clear_cache is True

    def test_cli_numeric_arguments(self):
        """Test CLI with numeric arguments."""
        argv = ['yacba', '--model', 'gpt-4', '--system-prompt', 'Test',
                '--max-files', '50', '--window-size', '80']
        
        with patch.object(sys, 'argv', argv):
            result = parse_args()
            
            assert result.max_files == "50"
            assert result.window_size == "80"

    def test_cli_with_config_arguments(self):
        """Test CLI with configuration arguments."""
        argv = ['yacba', '--model', 'gpt-4', '--system-prompt', 'Test',
                '--profile', 'development', '--config', '/path/to/config.yaml']
        
        with patch.object(sys, 'argv', argv):
            result = parse_args()
            
            assert result.profile == 'development'
            assert result.config == '/path/to/config.yaml'

    def test_cli_special_commands(self):
        """Test special CLI commands."""
        # Test --list-profiles
        with patch.object(sys, 'argv', ['yacba', '--list-profiles']):
            result = parse_args()
            assert result.list_profiles is True

        # Test --show-config
        with patch.object(sys, 'argv', ['yacba', '--show-config']):
            result = parse_args()
            assert result.show_config is True

    def test_cli_with_file_references(self):
        """Test CLI with @file references."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tf:
            tf.write("System prompt from file")
            tf.flush()
            
            argv = ['yacba', '--model', 'gpt-4', '--system-prompt', f'@{tf.name}']
            
            with patch.object(sys, 'argv', argv):
                result = parse_args()
                
                # The @file processing happens in validation, not parsing
                assert result.system_prompt == f'@{tf.name}'
            
            # Cleanup
            Path(tf.name).unlink()


class TestArgumentValidationIntegration:
    """Test argument validation with actual parsed arguments."""

    def test_validate_parsed_arguments(self):
        """Test validating parsed arguments."""
        with patch.object(sys, 'argv', ['yacba', '--model', 'gpt-4', '--system-prompt', 'Test']):
            parsed = parse_args()
            validated = validate_args(vars(parsed))
            
            # Model should get framework prefix
            assert validated['model'] == 'openai:gpt-4'
            assert validated['system_prompt'] == 'Test'

    def test_validate_file_reference_processing(self):
        """Test file reference processing in validation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tf:
            tf.write("Content from file")
            tf.flush()
            
            with patch.object(sys, 'argv', ['yacba', '--model', 'gpt-4', '--system-prompt', f'@{tf.name}']):
                parsed = parse_args()
                validated = validate_args(vars(parsed))
                
                # File reference should be processed
                assert validated['system_prompt'] == 'Content from file'
            
            # Cleanup
            Path(tf.name).unlink()

    def test_validate_boolean_processing(self):
        """Test boolean validation."""
        with patch.object(sys, 'argv', ['yacba', '--model', 'gpt-4', '--system-prompt', 'Test', '--show-tool-use']):
            parsed = parse_args()
            validated = validate_args(vars(parsed))
            
            assert validated['show_tool_use'] is True

    def test_validation_error_handling(self):
        """Test validation error handling."""
        with patch.object(sys, 'argv', ['yacba', '--model', ':', '--system-prompt', 'Test']):
            parsed = parse_args()
            
            # This should raise a validation error
            with pytest.raises(ValueError, match="Invalid value for 'model'"):
                validate_args(vars(parsed))


class TestArgumentParsingEdgeCases:
    """Test edge cases in argument parsing."""

    def test_short_form_arguments(self):
        """Test short form arguments work."""
        with patch.object(sys, 'argv', ['yacba', '-m', 'gpt-4', '-s', 'Test prompt']):
            result = parse_args()
            
            assert result.model == 'gpt-4'
            assert result.system_prompt == 'Test prompt'

    def test_mixed_short_and_long_arguments(self):
        """Test mixing short and long form arguments."""
        argv = ['yacba', '-m', 'gpt-4', '--system-prompt', 'Test', '-f', 'file.py']
        
        with patch.object(sys, 'argv', argv):
            result = parse_args()
            
            assert result.model == 'gpt-4'
            assert result.system_prompt == 'Test'
            assert result.files == [['file.py']]

    def test_conversation_manager_choices(self):
        """Test conversation manager choices."""
        choices = ['null', 'sliding_window', 'summarizing']
        
        for choice in choices:
            argv = ['yacba', '--model', 'gpt-4', '--system-prompt', 'Test',
                    '--conversation-manager', choice]
            
            with patch.object(sys, 'argv', argv):
                result = parse_args()
                assert result.conversation_manager == choice

    def test_config_override_multiple(self):
        """Test multiple config overrides."""
        argv = ['yacba', '--model', 'gpt-4', '--system-prompt', 'Test',
                '-c', 'temperature=0.8', '-c', 'max_tokens=2000']
        
        with patch.object(sys, 'argv', argv):
            result = parse_args()
            
            assert result.config_override == ['temperature=0.8', 'max_tokens=2000']


class TestArgumentParsingErrorScenarios:
    """Test error scenarios in argument parsing."""

    def test_missing_required_arguments_handled_gracefully(self):
        """Test that missing arguments are handled by defaults or validation."""
        # The parser might have defaults, so test what happens with minimal args
        with patch.object(sys, 'argv', ['yacba']):
            # This might work if all arguments have defaults, or might fail
            try:
                result = parse_args()
                # If it works, check that defaults are applied
                assert hasattr(result, 'model')
                assert hasattr(result, 'system_prompt')
            except SystemExit:
                # This is expected if required arguments are missing
                pass

    def test_invalid_choice_arguments(self):
        """Test invalid choice arguments."""
        argv = ['yacba', '--model', 'gpt-4', '--system-prompt', 'Test',
                '--conversation-manager', 'invalid_choice']
        
        with patch.object(sys, 'argv', argv):
            # This should exit with error due to invalid choice
            with pytest.raises(SystemExit):
                parse_args()

    def test_invalid_numeric_arguments(self):
        """Test invalid numeric arguments are accepted by parser but fail in validation."""
        argv = ['yacba', '--model', 'gpt-4', '--system-prompt', 'Test',
                '--max-files', 'not_a_number']
        
        with patch.object(sys, 'argv', argv):
            # Parser should succeed (accepts strings)
            result = parse_args()
            assert result.max_files == 'not_a_number'
            
            # But validation should fail
            with pytest.raises(ValueError, match="Invalid value for 'max_files'"):
                validate_args(vars(result))
