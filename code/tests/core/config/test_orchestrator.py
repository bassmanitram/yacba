"""
Clean tests for core.config.orchestrator module - WORKING VERSION.
"""

import pytest
from unittest.mock import patch, MagicMock

from core.config.orchestrator import parse_config


class TestParseConfigBasic:
    """Test basic parse_config functionality."""

    def test_parse_config_minimal(self):
        """Test parse_config with minimal arguments."""
        with patch('sys.argv', ['yacba', '--model', 'gpt-4', '--system-prompt', 'Test']):
            result = parse_config()
            
            # Should return a YacbaConfig object
            assert result is not None
            assert hasattr(result, 'model_string')
            assert result.model_string == 'openai:gpt-4'

    def test_parse_config_list_profiles(self):
        """Test --list-profiles command."""
        with patch('sys.argv', ['yacba', '--list-profiles']):
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
            with patch('core.config.orchestrator.ConfigManager') as mock_manager_class:
                mock_manager = MagicMock()
                mock_manager_class.return_value = mock_manager
                
                with patch('builtins.print') as mock_print:
                    with patch('sys.exit') as mock_exit:
                        parse_config()
                        
                        mock_manager.create_sample_config.assert_called_with(config_path)
                        mock_print.assert_called_with(f'Configuration file created at: {config_path}')
                        mock_exit.assert_called_with(0)