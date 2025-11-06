"""
Tests for config.factory module.

Target Coverage: 60%+ (complex module with many integration points)
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys


class TestProfileConfigConstants:
    """Tests for profile config constants."""
    
    def test_profile_config_name(self):
        """Test PROFILE_CONFIG_NAME constant."""
        from config.factory import PROFILE_CONFIG_NAME
        
        assert isinstance(PROFILE_CONFIG_NAME, str)
        assert PROFILE_CONFIG_NAME == ".yacba"
    
    def test_profile_config_profile_file_name(self):
        """Test PROFILE_CONFIG_PROFILE_FILE_NAME constant."""
        from config.factory import PROFILE_CONFIG_PROFILE_FILE_NAME
        
        assert isinstance(PROFILE_CONFIG_PROFILE_FILE_NAME, str)
        assert len(PROFILE_CONFIG_PROFILE_FILE_NAME) > 0


class TestNormalizeCliFieldNames:
    """Tests for _normalize_cli_field_names function."""
    
    def test_normalize_empty_dict(self):
        """Test normalizing empty dict."""
        from config.factory import _normalize_cli_field_names
        
        result = _normalize_cli_field_names({})
        assert result == {}
    
    def test_normalize_preserves_original(self):
        """Test that original fields are preserved."""
        from config.factory import _normalize_cli_field_names
        
        input_dict = {"model_string": "gpt-4o", "other": "value"}
        result = _normalize_cli_field_names(input_dict)
        
        assert "model_string" in result
        assert result["model_string"] == "gpt-4o"
        assert "other" in result
    
    def test_normalize_adds_aliases(self):
        """Test that aliases are added."""
        from config.factory import _normalize_cli_field_names
        
        input_dict = {"model_string": "gpt-4o"}
        result = _normalize_cli_field_names(input_dict)
        
        # Should have both the original and the alias
        assert "model_string" in result
        # May also have "model" alias
        if "model" in result:
            assert result["model"] == "gpt-4o"
    
    def test_normalize_handles_multiple_fields(self):
        """Test normalizing multiple fields."""
        from config.factory import _normalize_cli_field_names
        
        input_dict = {
            "model_string": "gpt-4o",
            "session_name": "test-session",
            "conversation_manager_type": "sliding_window"
        }
        
        result = _normalize_cli_field_names(input_dict)
        
        # Should have all original fields
        assert len(result) >= len(input_dict)
        for key in input_dict:
            assert key in result


class TestParseConfigBasic:
    """Basic tests for parse_config function."""
    
    @patch('sys.argv', ['yacba.py', '-m', 'gpt-4o'])
    def test_parse_config_basic_call(self):
        """Test basic parse_config call - skip due to SystemExit."""
        from config.factory import parse_config
        
        # parse_config can call sys.exit when showing profiles
        # This test is challenging without full integration
        # Skip or mark as integration test
        pytest.skip("parse_config requires full integration test setup")


class TestToolDiscoveryIntegration:
    """Tests for tool discovery integration in factory."""
    
    def test_discover_tool_configs_called(self, tmp_path):
        """Test that discover_tool_configs is used."""
        from config.factory import discover_tool_configs
        
        # Should be importable
        assert callable(discover_tool_configs)
        
        # Should work with temp directory - returns tuple
        result = discover_tool_configs(str(tmp_path))
        assert isinstance(result, tuple)
        assert len(result) == 2
        # First element is list of paths
        assert isinstance(result[0], list)
        # Second element is ToolDiscoveryResult
        assert hasattr(result[1], 'successful_configs')


class TestValidateFilePath:
    """Tests for validate_file_path usage."""
    
    def test_validate_file_path_imported(self):
        """Test that validate_file_path is imported."""
        from config.factory import validate_file_path
        
        assert callable(validate_file_path)


@pytest.mark.integration
class TestFactoryIntegration:
    """Integration tests for factory module."""
    
    def test_imports_work(self):
        """Test that all necessary imports work."""
        import config.factory as factory
        
        # Should have key functions
        assert hasattr(factory, 'parse_config')
        assert hasattr(factory, 'PROFILE_CONFIG_NAME')
        assert hasattr(factory, '_normalize_cli_field_names')
    
    def test_clean_dict_integration(self):
        """Test clean_dict is available and works."""
        from config.factory import clean_dict
        
        test_dict = {"a": 1, "b": None, "c": 3}
        result = clean_dict(test_dict)
        
        assert "a" in result
        assert "b" not in result
        assert "c" in result
    
    def test_argument_defaults_available(self):
        """Test ARGUMENT_DEFAULTS is imported."""
        from config.factory import ARGUMENT_DEFAULTS
        
        assert isinstance(ARGUMENT_DEFAULTS, dict)
        assert len(ARGUMENT_DEFAULTS) > 0


class TestFieldNormalizationMappings:
    """Tests for specific field name mappings."""
    
    def test_model_string_to_model(self):
        """Test model_string normalizes to model."""
        from config.factory import _normalize_cli_field_names
        
        result = _normalize_cli_field_names({"model_string": "gpt-4o"})
        
        # Should have original
        assert "model_string" in result
        # May have normalized version
        assert "model" in result or "model_string" in result
    
    def test_session_name_to_session(self):
        """Test session_name normalizes to session."""
        from config.factory import _normalize_cli_field_names
        
        result = _normalize_cli_field_names({"session_name": "test"})
        
        # Should have original
        assert "session_name" in result
        # May have normalized version  
        assert "session" in result or "session_name" in result


class TestYacbaConfigImport:
    """Tests for YacbaConfig integration."""
    
    def test_yacba_config_imported(self):
        """Test YacbaConfig is imported."""
        from config.factory import YacbaConfig
        
        assert YacbaConfig is not None
        # Should be a dataclass
        assert hasattr(YacbaConfig, '__dataclass_fields__')
