"""
Clean tests for core.config.orchestrator module - WORKING VERSION.
"""

import pytest
from unittest.mock import patch, MagicMock

from core.config.orchestrator import parse_config, ConfigManager


class TestParseConfigBasic:
    """Test basic parse_config functionality."""

    def test_parse_config_minimal(self):
        """Test parse_config with minimal arguments."""
        with patch.object(ConfigManager, 'load_config', return_value={}):
            with patch('sys.argv', ['yacba', '--model', 'gpt-4', '--system-prompt', 'Test']):
                result = parse_config()
                
                # Should return a YacbaConfig object
                assert result is not None
                assert hasattr(result, 'model_string')
                assert result.model_string == 'openai:gpt-4'

    def test_parse_config_list_profiles(self):
        """Test --list-profiles command."""
        with patch('sys.argv', ['yacba', '--list-profiles']):
            with patch.object(ConfigManager, 'load_config', return_value={}):
                with patch('core.config.orchestrator.ConfigManager') as mock_manager_class:
                    mock_manager = MagicMock()
                    mock_manager.list_profiles.return_value = ['dev', 'prod', 'test']
                    mock_manager_class.return_value = mock_manager
                    
                    with patch('builtins.print') as mock_print:
                        with patch('sys.exit') as mock_exit:
                            parse_config()
                            
                            mock_print.assert_any_call("Available profiles:")
                            mock_print.assert_any_call("  - dev")
                            mock_print.assert_any_call("  - prod")
                            mock_print.assert_any_call("  - test")
                            mock_exit.assert_called_with(0)

    def test_parse_config_init_config(self):
        """Test --init-config command."""
        import tempfile
        import os
        
        # Use a valid temporary directory path
        temp_dir = tempfile.gettempdir()
        config_path = os.path.join(temp_dir, 'test_config.yaml')
        
        with patch('sys.argv', ['yacba', '--init-config', config_path]):
            with patch.object(ConfigManager, 'load_config', return_value={}):
                with patch('core.config.orchestrator.ConfigManager') as mock_manager_class:
                    mock_manager = MagicMock()
                    mock_manager_class.return_value = mock_manager
                    
                    with patch('builtins.print') as mock_print:
                        with patch('sys.exit') as mock_exit:
                            parse_config()
                            
                            mock_manager.create_sample_config.assert_called_with(config_path)
                            mock_print.assert_called_with(f'Configuration file created at: {config_path}')
                            mock_exit.assert_called_with(0)


class TestParseConfigUICustomization:
    """Test parse_config functionality with UI customization options."""

    def test_parse_config_with_ui_customization(self):
        """Test parse_config with UI customization arguments."""
        with patch.object(ConfigManager, 'load_config', return_value={}):
            with patch('sys.argv', [
                'yacba', 
                '--model', 'gpt-4', 
                '--system-prompt', 'Test',
                '--cli-prompt', '<b><skyblue>You: </skyblue></b>',
                '--response-prefix', '<b><seagreen>Chatbot: </seagreen></b>'
            ]):
                result = parse_config()
                
                # Should return a YacbaConfig object with UI customization
                assert result is not None
                assert hasattr(result, 'cli_prompt')
                assert hasattr(result, 'response_prefix')
                assert result.cli_prompt == '<b><skyblue>You: </skyblue></b>'
                assert result.response_prefix == '<b><seagreen>Chatbot: </seagreen></b>'
                assert result.model_string == 'openai:gpt-4'

    def test_parse_config_ui_customization_optional(self):
        """Test parse_config without UI customization arguments."""
        with patch.object(ConfigManager, 'load_config', return_value={}):
            with patch('sys.argv', ['yacba', '--model', 'gpt-4', '--system-prompt', 'Test']):
                result = parse_config()
                
                # Should return a YacbaConfig object with None UI customization
                assert result is not None
                assert hasattr(result, 'cli_prompt')
                assert hasattr(result, 'response_prefix')
                assert result.cli_prompt == "<b><ansigreen>You:</ansigreen></b> "
                assert result.response_prefix == "<b><darkcyan>Chatbot:</darkcyan></b> "

    def test_parse_config_ui_customization_only_cli_prompt(self):
        """Test parse_config with only --cli-prompt specified."""
        with patch.object(ConfigManager, 'load_config', return_value={}):
            with patch('sys.argv', [
                'yacba', 
                '--model', 'gpt-4', 
                '--system-prompt', 'Test',
                '--cli-prompt', '<b>Custom You: </b>'
            ]):
                result = parse_config()
                
                assert result.cli_prompt == '<b>Custom You: </b>'
                assert result.response_prefix == "<b><darkcyan>Chatbot:</darkcyan></b> "

    def test_parse_config_ui_customization_only_response_prefix(self):
        """Test parse_config with only --response-prefix specified."""
        with patch.object(ConfigManager, 'load_config', return_value={}):
            with patch('sys.argv', [
                'yacba', 
                '--model', 'gpt-4', 
                '--system-prompt', 'Test',
                '--response-prefix', '<b>Bot Response: </b>'
            ]):
                result = parse_config()
                
                assert result.cli_prompt == "<b><ansigreen>You:</ansigreen></b> "
                assert result.response_prefix == '<b>Bot Response: </b>'

    def test_parse_config_ui_customization_complex_html(self):
        """Test parse_config with complex HTML formatting."""
        complex_cli_prompt = '<div class="user-prompt"><b style="color: #4A90E2">👤 <span>You</span>:</b></div>'
        complex_response_prefix = '<div class="bot-response"><b style="color: #50C878">🤖 <span>Assistant</span>:</b> '
        
        with patch.object(ConfigManager, 'load_config', return_value={}):
            with patch('sys.argv', [
                'yacba', 
                '--model', 'gpt-4', 
                '--system-prompt', 'Test',
                '--cli-prompt', complex_cli_prompt,
                '--response-prefix', complex_response_prefix
            ]):
                result = parse_config()
                
                assert result.cli_prompt == complex_cli_prompt
                assert result.response_prefix == complex_response_prefix

    def test_parse_config_ui_customization_empty_strings(self):
        """Test parse_config with empty string UI customization."""
        with patch.object(ConfigManager, 'load_config', return_value={}):
            with patch('sys.argv', [
                'yacba', 
                '--model', 'gpt-4', 
                '--system-prompt', 'Test',
                '--cli-prompt', '',
                '--response-prefix', ''
            ]):
                result = parse_config()
                
                assert result.cli_prompt == ''
                assert result.response_prefix == ''

    def test_parse_config_ui_customization_with_other_options(self):
        """Test parse_config with UI customization and other options."""
        with patch.object(ConfigManager, 'load_config', return_value={}):
            with patch('sys.argv', [
                'yacba', 
                '--model', 'litellm:gemini/gemini-1.5-flash',
                '--system-prompt', 'You are a helpful assistant',
                '--cli-prompt', '<b><blue>You:</blue></b> ',
                '--response-prefix', '<b><green>AI:</green></b> ',
                '--headless',
                '--initial-message', 'Hello world',
                '--show-tool-use',
                '--max-files', '15'
            ]):
                result = parse_config()
                
                # Check UI customization
                assert result.cli_prompt == '<b><blue>You:</blue></b> '
                assert result.response_prefix == '<b><green>AI:</green></b> '
                
                # Check other options still work
                assert result.model_string == 'litellm:gemini/gemini-1.5-flash'
                assert result.headless is True
                assert result.initial_message == 'Hello world'
                assert result.show_tool_use is True
                assert result.max_files == 15

    def test_parse_config_ui_customization_in_config_merging(self):
        """Test that UI customization participates in config merging pipeline."""
        with patch.object(ConfigManager, 'load_config', return_value={
            'response_prefix': '<b>Config Bot: </b>',
            'model': 'config-model'
        }):
            with patch('sys.argv', [
                'yacba', 
                '--model', 'gpt-4', 
                '--system-prompt', 'Test',
                '--cli-prompt', '<b>CLI You: </b>'
            ]):
                result = parse_config()
                
                # CLI should override config file for cli_prompt
                assert result.cli_prompt == '<b>CLI You: </b>'
                # Config file should provide response_prefix since not in CLI
                assert result.response_prefix == '<b>Config Bot: </b>'
                # CLI should override config file for model
                assert 'gpt-4' in result.model_string
