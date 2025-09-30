"""
Integration tests for orchestrator - end-to-end configuration scenarios.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
from argparse import Namespace

from core.config.orchestrator import parse_config
from core.config.dataclass import YacbaConfig
from yacba_types.config import ToolDiscoveryResult


class TestOrchestratorIntegration:
    """Test end-to-end configuration integration scenarios."""

    @patch('core.config.orchestrator.parse_args')
    @patch('core.config.orchestrator.discover_tool_configs')
    @patch('core.config.orchestrator._create_model_config')
    def test_config_merging_precedence(self, mock_model_config, mock_discover, mock_parse_args):
        """Test configuration merging with proper precedence: CLI > config file > defaults."""
        # Create a config file
        config_data = {
            'default_profile': 'test',
            'defaults': {
                'model': 'config-default-model',
                'temperature': 0.5,
                'max_files': 15
            },
            'profiles': {
                'test': {
                    'model': 'config-profile-model',
                    'show_tool_use': True,
                    'max_files': 25
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tf:
            yaml.dump(config_data, tf)
            tf.flush()
            
            # Mock CLI args that should override config file
            mock_parse_args.return_value = Namespace(
                model='cli-model',  # Should override config file
                system_prompt='CLI prompt',
                max_files=30,  # Should override config file
                show_tool_use=False,  # Should override config file
                config=tf.name,
                profile='test',
                files=None,
                tool_configs_dir=None,
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
                clear_cache=False,
                show_perf_stats=False,
                disable_cache=False
            )
            
            mock_discover.return_value = ([], ToolDiscoveryResult([], [], 0))
            mock_model_config.return_value = {}
            
            with patch('core.config.orchestrator.validate_args', side_effect=lambda x: x):
                result = parse_config()
            
            # CLI values should override config file values
            assert result.model_string == 'cli-model'  # From CLI
            assert result.system_prompt == 'CLI prompt'  # From CLI
            assert result.max_files == 30  # From CLI
            assert result.show_tool_use is False  # From CLI
            
            # Cleanup
            Path(tf.name).unlink()

    @patch('core.config.orchestrator.parse_args')
    @patch('core.config.orchestrator.discover_tool_configs')
    @patch('core.config.orchestrator._create_model_config')
    def test_config_with_inheritance_and_variables(self, mock_model_config, mock_discover, mock_parse_args):
        """Test configuration with profile inheritance and variable substitution."""
        config_data = {
            'profiles': {
                'base': {
                    'model': 'gpt-4',
                    'temperature': 0.5,
                    'config_dir': '${HOME}/.yacba'
                },
                'development': {
                    'inherits': 'base',
                    'model': 'claude-3',
                    'show_tool_use': True,
                    'project_name': '${PROJECT_NAME}'
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tf:
            yaml.dump(config_data, tf)
            tf.flush()
            
            mock_parse_args.return_value = Namespace(
                system_prompt='Test prompt',
                config=tf.name,
                profile='development',
                files=None,
                tool_configs_dir=None,
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
                show_tool_use=None,  # Should come from config
                clear_cache=False,
                show_perf_stats=False,
                disable_cache=False,
                max_files=20,
                model=None  # Should come from config
            )
            
            mock_discover.return_value = ([], ToolDiscoveryResult([], [], 0))
            mock_model_config.return_value = {}
            
            with patch.dict('os.environ', {'HOME': '/home/testuser'}):
                with patch('pathlib.Path.cwd', return_value=Path('/projects/myapp')):
                    with patch('core.config.orchestrator.validate_args', side_effect=lambda x: x):
                        result = parse_config()
            
            # Should get values from inheritance chain with variable substitution
            assert result.model_string == 'claude-3'  # From development profile
            assert result.show_tool_use is True  # From development profile
            # Note: config_dir and project_name are not direct YacbaConfig fields,
            # so we can't test them directly without modifying the orchestrator
            
            # Cleanup
            Path(tf.name).unlink()

    @patch('core.config.orchestrator.parse_args')
    @patch('core.config.orchestrator.discover_tool_configs')
    @patch('core.config.orchestrator._create_model_config')
    def test_files_and_tools_integration(self, mock_model_config, mock_discover, mock_parse_args):
        """Test integration with file uploads and tool discovery."""
        # Create test files
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f1:
            f1.write(b"Test file content")
            f1.flush()
            
            # Mock tool discovery
            mock_tool_configs = [{'id': 'test_tool', 'type': 'python', 'disabled': False}]
            mock_discovery_result = ToolDiscoveryResult(
                successful_configs=mock_tool_configs,
                failed_configs=[],
                total_files_scanned=1
            )
            mock_discover.return_value = (mock_tool_configs, mock_discovery_result)
            
            mock_parse_args.return_value = Namespace(
                model='gpt-4',
                system_prompt='Test prompt',
                files=[[f1.name, 'text/plain']],
                tool_configs_dir='/path/to/tools',
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
            
            mock_model_config.return_value = {'temperature': 0.7}
            
            with patch('core.config.orchestrator.validate_args', side_effect=lambda x: x):
                result = parse_config()
            
            # Check file uploads were processed
            assert len(result.files_to_upload) == 1
            assert result.files_to_upload[0]['mimetype'] == 'text/plain'
            assert result.files_to_upload[0]['path'] == str(Path(f1.name).resolve())
            
            # Check tool discovery was called and results stored
            assert result.tool_configs == mock_tool_configs
            assert result.tool_discovery_result == mock_discovery_result
            mock_discover.assert_called_with('/path/to/tools')
            
            # Check model config was processed
            assert result.model_config == {'temperature': 0.7}
            
            # Cleanup
            Path(f1.name).unlink()

    @patch('core.config.orchestrator.parse_args')
    @patch('sys.exit')
    def test_error_handling_configuration_error(self, mock_exit, mock_parse_args):
        """Test error handling when configuration parsing fails."""
        mock_parse_args.side_effect = Exception("Parse error")
        
        # Should catch exception and exit with error code 1
        parse_config()
        mock_exit.assert_called_with(1)

    @patch('core.config.orchestrator.parse_args')
    @patch('core.config.orchestrator.discover_tool_configs')
    @patch('core.config.orchestrator._create_model_config')
    def test_headless_mode_configuration(self, mock_model_config, mock_discover, mock_parse_args):
        """Test headless mode configuration."""
        mock_parse_args.return_value = Namespace(
            model='gpt-4',
            system_prompt='Test prompt',
            headless=True,
            initial_message='Hello, world!',
            files=None,
            tool_configs_dir=None,
            config=None,
            profile=None,
            list_profiles=False,
            init_config=None,
            show_config=False,
            config_override=None,
            model_config=None,
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
        
        mock_discover.return_value = ([], ToolDiscoveryResult([], [], 0))
        mock_model_config.return_value = {}
        
        with patch('core.config.orchestrator.validate_args', side_effect=lambda x: x):
            result = parse_config()
        
        assert result.headless is True
        assert result.initial_message == 'Hello, world!'
        assert result.is_interactive is False

    def test_backward_compatibility_wrapper(self):
        """Test that orchestrate_config_parsing wrapper works."""
        with patch('core.config.orchestrator.parse_config') as mock_parse:
            mock_config = MagicMock(spec=YacbaConfig)
            mock_parse.return_value = mock_config
            
            from core.config.orchestrator import orchestrate_config_parsing
            result = orchestrate_config_parsing()
            
            assert result == mock_config
            mock_parse.assert_called_once()