"""
Integration tests for UI customization CLI options.

Tests the complete end-to-end flow of --cli-prompt and --response-prefix
arguments through the CLI configuration system.
"""

import pytest
from unittest.mock import patch

from core.config.orchestrator import parse_config, ConfigManager
from core.config.dataclass import YacbaConfig


class TestUICustomizationIntegration:
    """Integration tests for UI customization CLI options."""

    def test_end_to_end_ui_customization_cli_only(self):
        """Test complete CLI-only UI customization flow."""
        with patch.object(ConfigManager, 'load_config', return_value={}):
            test_argv = [
                'yacba',
                '--model', 'litellm:gemini/gemini-1.5-flash',
                '--system-prompt', 'You are a helpful assistant with custom UI.',
                '--cli-prompt', '<b><skyblue>👤 You: </skyblue></b>',
                '--response-prefix', '<b><seagreen>🤖 Assistant: </seagreen></b>',
                '--show-tool-use',
                '--max-files', '20'
            ]
            
            with patch('sys.argv', test_argv):
                config = parse_config()
                
                # Verify UI customization
                assert config.cli_prompt == '<b><skyblue>👤 You: </skyblue></b>'
                assert config.response_prefix == '<b><seagreen>🤖 Assistant: </seagreen></b>'
                
                # Verify other config still works
                assert config.model_string == 'litellm:gemini/gemini-1.5-flash'
                assert config.show_tool_use is True
                assert config.max_files == 20

    def test_ui_customization_only_cli_prompt(self):
        """Test CLI with only cli_prompt specified."""
        with patch.object(ConfigManager, 'load_config', return_value={}):
            test_argv = [
                'yacba',
                '--model', 'gpt-4',
                '--system-prompt', 'Test',
                '--cli-prompt', '<b>Only You: </b>'
            ]
            
            with patch('sys.argv', test_argv):
                config = parse_config()
                
                assert config.cli_prompt == '<b>Only You: </b>'
                assert config.response_prefix == "<b><darkcyan>Chatbot:</darkcyan></b> "

    def test_ui_customization_only_response_prefix(self):
        """Test CLI with only response_prefix specified."""
        with patch.object(ConfigManager, 'load_config', return_value={}):
            test_argv = [
                'yacba',
                '--model', 'gpt-4',
                '--system-prompt', 'Test',
                '--response-prefix', '<b>Only Bot: </b>'
            ]
            
            with patch('sys.argv', test_argv):
                config = parse_config()
                
                assert config.cli_prompt == "<b><ansigreen>You:</ansigreen></b> "
                assert config.response_prefix == '<b>Only Bot: </b>'
