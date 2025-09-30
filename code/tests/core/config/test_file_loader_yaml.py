"""
Tests for YAML file loading and parsing functionality.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

from core.config.file_loader import ConfigFileLoader, ConfigFile


class TestConfigFileLoader:
    """Test ConfigFileLoader file discovery and loading."""

    def test_discover_config_explicit_path_exists(self):
        """Test config discovery with explicit path that exists."""
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tf:
            tf.write(b"test: config")
            tf.flush()
            
            result = ConfigFileLoader.discover_config_file(tf.name)
            assert result == Path(tf.name).resolve()
            
            # Cleanup
            Path(tf.name).unlink()

    def test_discover_config_explicit_path_missing(self):
        """Test config discovery with explicit path that doesn't exist."""
        missing_path = "/tmp/nonexistent_config_12345.yaml"
        result = ConfigFileLoader.discover_config_file(missing_path)
        assert result is None

    @patch('pathlib.Path.exists')
    def test_discover_config_search_paths(self, mock_exists):
        """Test config discovery through search paths."""
        # Mock the first search path to exist
        mock_exists.side_effect = lambda: str(self) == str(Path("./.yacba/config.yaml").resolve())
        
        with patch('pathlib.Path.is_file', return_value=True):
            result = ConfigFileLoader.discover_config_file()
            expected = Path("./.yacba/config.yaml").resolve()
            assert result == expected

    @patch('pathlib.Path.exists', return_value=False)
    def test_discover_config_no_file_found(self, mock_exists):
        """Test config discovery when no config file exists."""
        result = ConfigFileLoader.discover_config_file()
        assert result is None

    def test_load_config_file_missing(self):
        """Test loading non-existent config file."""
        missing_path = "/tmp/nonexistent_config_12345.yaml"
        
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            ConfigFileLoader.load_config_file(missing_path)

    def test_load_simple_yaml_config(self):
        """Test loading simple YAML configuration."""
        config_data = {
            'default_profile': 'dev',
            'defaults': {'model': 'gpt-4', 'temperature': 0.5},
            'profiles': {
                'dev': {'show_tool_use': True, 'temperature': 0.7}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tf:
            yaml.dump(config_data, tf)
            tf.flush()
            
            result = ConfigFileLoader.load_config_file(tf.name)
            
            assert isinstance(result, ConfigFile)
            assert result.default_profile == 'dev'
            assert result.defaults == {'model': 'gpt-4', 'temperature': 0.5}
            assert 'dev' in result.profiles
            assert result.profiles['dev'].name == 'dev'
            assert result.profiles['dev'].settings == {'show_tool_use': True, 'temperature': 0.7}
            
            # Cleanup
            Path(tf.name).unlink()

    def test_load_config_with_inheritance(self):
        """Test loading config with profile inheritance."""
        config_data = {
            'profiles': {
                'base': {
                    'model': 'gpt-4',
                    'temperature': 0.5
                },
                'development': {
                    'inherits': 'base',
                    'temperature': 0.7,
                    'show_tool_use': True
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tf:
            yaml.dump(config_data, tf)
            tf.flush()
            
            result = ConfigFileLoader.load_config_file(tf.name)
            
            # Check inheritance is parsed correctly
            dev_profile = result.profiles['development']
            assert dev_profile.inherits == 'base'
            assert dev_profile.settings == {'temperature': 0.7, 'show_tool_use': True}
            
            # Check resolved settings
            resolved = result.get_profile_settings('development')
            expected = {
                'model': 'gpt-4',           # From base
                'temperature': 0.7,         # Overridden in development
                'show_tool_use': True       # Added in development
            }
            assert resolved == expected
            
            # Cleanup
            Path(tf.name).unlink()

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML file."""
        invalid_yaml = "invalid: yaml: content: [unclosed"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tf:
            tf.write(invalid_yaml)
            tf.flush()
            
            with pytest.raises(Exception):  # Should raise YAML parsing error
                ConfigFileLoader.load_config_file(tf.name)
            
            # Cleanup
            Path(tf.name).unlink()

    def test_parse_config_data_minimal(self):
        """Test parsing minimal config data."""
        data = {}
        result = ConfigFileLoader._parse_config_data(data, Path("/test.yaml"))
        
        assert result.default_profile is None
        assert result.defaults == {}
        assert result.profiles == {}

    def test_parse_config_data_invalid_profile(self):
        """Test parsing config with invalid profile data."""
        data = {
            'profiles': {
                'valid': {'model': 'gpt-4'},
                'invalid': 'not-a-dict'  # Invalid profile data
            }
        }
        
        result = ConfigFileLoader._parse_config_data(data, Path("/test.yaml"))
        
        # Should skip invalid profile but keep valid one
        assert 'valid' in result.profiles
        assert 'invalid' not in result.profiles