"""
Tests for core.config.orchestrator module - end-to-end configuration integration.
"""

import pytest
import tempfile
import yaml
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from argparse import Namespace

from core.config.orchestrator import (
    parse_config,
    orchestrate_config_parsing,
    _process_file_uploads,
    _create_model_config
)
from core.config.dataclass import YacbaConfig
from yacba_types.config import FileUpload, ToolDiscoveryResult


class TestProcessFileUploads:
    """Test file upload processing functionality."""

    def test_process_file_uploads_valid_files(self):
        """Test processing valid file uploads."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f1:
            f1.write(b"Test content 1")
            f1.flush()
            
            with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f2:
                f2.write(b"# Test Python file")
                f2.flush()
                
                file_paths = [
                    [f1.name, 'text/plain'],
                    [f2.name, 'text/x-python']
                ]
                
                result = _process_file_uploads(file_paths)
                
                assert len(result) == 2
                assert result[0]['path'] == str(Path(f1.name).resolve())
                assert result[0]['mimetype'] == 'text/plain'
                assert result[0]['size'] > 0
                
                assert result[1]['path'] == str(Path(f2.name).resolve())
                assert result[1]['mimetype'] == 'text/x-python'
                assert result[1]['size'] > 0
                
                # Cleanup
                Path(f1.name).unlink()
                Path(f2.name).unlink()

    def test_process_file_uploads_missing_file(self):
        """Test processing non-existent file."""
        file_paths = [
            ['/tmp/nonexistent_file_12345.txt', 'text/plain']
        ]
        
        with pytest.raises(FileNotFoundError, match="File not found or not accessible"):
            _process_file_uploads(file_paths)

    def test_process_file_uploads_empty_list(self):
        """Test processing empty file list."""
        result = _process_file_uploads([])
        assert result == []


class TestCreateModelConfig:
    """Test model configuration creation."""

    def test_create_model_config_no_config(self):
        """Test creating model config with no inputs."""
        with patch('core.config.orchestrator.parse_model_config', return_value={}):
            result = _create_model_config()
            assert result == {}

    def test_create_model_config_with_file(self):
        """Test creating model config from file."""
        mock_config = {'temperature': 0.7, 'max_tokens': 2000}
        
        with patch('core.config.orchestrator.parse_model_config', return_value=mock_config):
            result = _create_model_config(model_config_file='/path/to/config.json')
            assert result == mock_config

    def test_create_model_config_with_overrides(self):
        """Test creating model config with overrides."""
        mock_config = {'temperature': 0.8, 'custom_param': 'value'}
        overrides = ['temperature=0.8', 'custom_param=value']
        
        with patch('core.config.orchestrator.parse_model_config', return_value=mock_config):
            result = _create_model_config(model_config_overrides=overrides)
            assert result == mock_config

    def test_create_model_config_error_handling(self):
        """Test model config error handling."""
        from utils.model_config_parser import ModelConfigError
        
        with patch('core.config.orchestrator.parse_model_config', 
                   side_effect=ModelConfigError("Invalid config")):
            with pytest.raises(ValueError, match="Model configuration error"):
                _create_model_config(model_config_file='/invalid/config.json')


class TestParseConfigBasic:
    """Test basic parse_config functionality."""

    @patch('core.config.orchestrator.parse_args')
    @patch('core.config.orchestrator.ConfigManager')
    @patch('core.config.orchestrator.discover_tool_configs')
    @patch('core.config.orchestrator._create_model_config')
    def test_parse_config_minimal(self, mock_model_config, mock_discover, 
                                  mock_config_manager, mock_parse_args):
        """Test parse_config with minimal configuration."""
        # Setup mocks
        mock_parse_args.return_value = Namespace(
            model='gpt-4',
            system_prompt='Test prompt',
            files=None,
            tool_configs_dir=None,
            config=None,
            profile=None,
            list_profiles=False,
            init_config=None,
            show_config=False,
            config_override=None,
            model_config=None,
            headless=False,
            initial_message=None,
            emulate_system_prompt=False,
            session=None,
            agent_id=None,
            conversation_manager='sliding_window',
            window_size=40,
            preserve_recent=10,
            summary_ratio=0.3,
            summarization_model=None,
            custom_summarization_prompt=None,
            no_truncate_results=False,
            show_tool_use=False,
            clear_cache=False,
            show_perf_stats=False,
            disable_cache=False,
            max_files=20
        )
        
        mock_manager = MagicMock()
        mock_manager.load_config.return_value = {}
        mock_config_manager.return_value = mock_manager
        
        mock_discover.return_value = ([], ToolDiscoveryResult([], [], 0))
        mock_model_config.return_value = {}
        
        # Mock validation
        with patch('core.config.orchestrator.validate_args', side_effect=lambda x: x):
            result = parse_config()
        
        assert isinstance(result, YacbaConfig)
        assert result.model_string == 'gpt-4'
        assert result.system_prompt == 'Test prompt'
        assert result.tool_configs == []
        assert result.files_to_upload == []

    @patch('core.config.orchestrator.parse_args')
    @patch('sys.exit')
    def test_parse_config_list_profiles(self, mock_exit, mock_parse_args):
        """Test --list-profiles command."""
        mock_parse_args.return_value = Namespace(
            list_profiles=True,
            config=None,
            profile=None
        )
        
        with patch('core.config.orchestrator.ConfigManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.list_profiles.return_value = ['dev', 'prod', 'test']
            mock_manager_class.return_value = mock_manager
            
            with patch('builtins.print') as mock_print:
                parse_config()
                
                mock_print.assert_any_call("Available profiles:")
                mock_print.assert_any_call("  - dev")
                mock_print.assert_any_call("  - prod") 
                mock_print.assert_any_call("  - test")
                mock_exit.assert_called_with(0)

    @patch('core.config.orchestrator.parse_args')
    @patch('sys.exit')
    def test_parse_config_init_config(self, mock_exit, mock_parse_args):
        """Test --init-config command."""
        mock_parse_args.return_value = Namespace(
            list_profiles=False,
            init_config='/path/to/config.yaml'
        )
        
        with patch('core.config.orchestrator.ConfigManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            
            with patch('builtins.print') as mock_print:
                parse_config()
                
                mock_manager.create_sample_config.assert_called_with('/path/to/config.yaml')
                mock_print.assert_called_with("Configuration file created at: /path/to/config.yaml")
                mock_exit.assert_called_with(0)