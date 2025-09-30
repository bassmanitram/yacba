"""
Tests for ConfigManager integration functionality.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch

from core.config.file_loader import ConfigManager


class TestConfigManager:
    """Test ConfigManager integration."""

    def test_config_manager_no_config_file(self):
        """Test ConfigManager when no config file is found."""
        manager = ConfigManager()
        
        with patch('core.config.file_loader.ConfigFileLoader.discover_config_file', return_value=None):
            result = manager.load_config()
        
        assert result == {}
        assert manager.config_file is None
        assert manager.current_profile is None

    def test_config_manager_load_simple_config(self):
        """Test ConfigManager loading a simple config file."""
        config_data = {
            'default_profile': 'dev',
            'defaults': {'model': 'gpt-4', 'temperature': 0.5},
            'profiles': {
                'dev': {'show_tool_use': True, 'max_files': 20}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tf:
            yaml.dump(config_data, tf)
            tf.flush()
            
            manager = ConfigManager()
            result = manager.load_config(tf.name)
            
            expected = {
                'model': 'gpt-4',           # From defaults
                'temperature': 0.5,         # From defaults  
                'show_tool_use': True,      # From dev profile
                'max_files': 20             # From dev profile
            }
            assert result == expected
            assert manager.current_profile is None  # No explicit profile specified
            
            # Cleanup
            Path(tf.name).unlink()

    def test_config_manager_explicit_profile(self):
        """Test ConfigManager with explicit profile selection."""
        config_data = {
            'default_profile': 'dev',
            'profiles': {
                'dev': {'model': 'claude', 'temperature': 0.8},
                'prod': {'model': 'gpt-4', 'temperature': 0.2}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tf:
            yaml.dump(config_data, tf)
            tf.flush()
            
            manager = ConfigManager()
            result = manager.load_config(tf.name, profile='prod')
            
            expected = {
                'model': 'gpt-4',
                'temperature': 0.2
            }
            assert result == expected
            assert manager.current_profile == 'prod'
            
            # Cleanup
            Path(tf.name).unlink()

    def test_config_manager_with_variables(self):
        """Test ConfigManager with variable substitution."""
        config_data = {
            'profiles': {
                'local': {
                    'model': 'gpt-4',
                    'config_dir': '${HOME}/.yacba',
                    'project': '${PROJECT_NAME}'
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tf:
            yaml.dump(config_data, tf)
            tf.flush()
            
            manager = ConfigManager()
            
            with patch.dict('os.environ', {'HOME': '/home/test'}):
                with patch('pathlib.Path.cwd', return_value=Path('/projects/myapp')):
                    result = manager.load_config(tf.name, profile='local')
            
            expected = {
                'model': 'gpt-4',
                'config_dir': '/home/test/.yacba',
                'project': 'myapp'
            }
            assert result == expected
            
            # Cleanup
            Path(tf.name).unlink()

    def test_config_manager_list_profiles(self):
        """Test ConfigManager profile listing."""
        config_data = {
            'profiles': {
                'dev': {'model': 'claude'},
                'prod': {'model': 'gpt-4'},
                'test': {'model': 'local'}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tf:
            yaml.dump(config_data, tf)
            tf.flush()
            
            manager = ConfigManager()
            manager.load_config(tf.name)
            
            profiles = manager.list_profiles()
            assert set(profiles) == {'dev', 'prod', 'test'}
            
            # Cleanup
            Path(tf.name).unlink()

    def test_config_manager_list_profiles_no_config(self):
        """Test listing profiles when no config is loaded."""
        manager = ConfigManager()
        profiles = manager.list_profiles()
        assert profiles == []

    def test_config_manager_get_resolved_config(self):
        """Test getting resolved config for debugging."""
        config_data = {
            'default_profile': 'dev',
            'defaults': {'temperature': 0.5},
            'profiles': {
                'dev': {'model': 'claude', 'temperature': 0.8},
                'prod': {'model': 'gpt-4'}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tf:
            yaml.dump(config_data, tf)
            tf.flush()
            
            manager = ConfigManager()
            manager.load_config(tf.name)
            
            # Test default profile resolution
            default_config = manager.get_resolved_config()
            expected_default = {
                'temperature': 0.8,  # Overridden in dev profile
                'model': 'claude'    # From dev profile
            }
            assert default_config == expected_default
            
            # Test explicit profile resolution
            prod_config = manager.get_resolved_config('prod')
            expected_prod = {
                'temperature': 0.5,  # From defaults
                'model': 'gpt-4'     # From prod profile
            }
            assert prod_config == expected_prod
            
            # Cleanup
            Path(tf.name).unlink()

    def test_config_manager_error_handling(self):
        """Test ConfigManager error handling."""
        # Create invalid YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tf:
            tf.write("invalid: yaml: [unclosed")
            tf.flush()
            
            manager = ConfigManager()
            result = manager.load_config(tf.name)
            
            # Should return empty dict on error
            assert result == {}
            assert manager.config_file is None
            
            # Cleanup
            Path(tf.name).unlink()

    def test_config_manager_create_sample_config(self):
        """Test creating sample configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "sample_config.yaml"
            
            manager = ConfigManager()
            manager.create_sample_config(output_path)
            
            assert output_path.exists()
            
            # Load and verify structure
            with open(output_path) as f:
                config = yaml.safe_load(f)
            
            assert 'default_profile' in config
            assert 'defaults' in config
            assert 'profiles' in config
            assert 'development' in config['profiles']
            assert 'production' in config['profiles']
            assert 'coding' in config['profiles']