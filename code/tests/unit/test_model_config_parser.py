"""
Tests for utils.model_config_parser module.

Target Coverage: 90%+
"""

import pytest
from pathlib import Path
import json


class TestModelConfigError:
    """Tests for ModelConfigError exception."""
    
    def test_model_config_error_raised(self):
        """Test ModelConfigError can be raised and caught."""
        from utils.model_config_parser import ModelConfigError
        
        with pytest.raises(ModelConfigError):
            raise ModelConfigError("Test error")
    
    def test_model_config_error_message(self):
        """Test ModelConfigError preserves message."""
        from utils.model_config_parser import ModelConfigError
        
        msg = "Configuration invalid"
        try:
            raise ModelConfigError(msg)
        except ModelConfigError as e:
            assert str(e) == msg


class TestModelConfigParser:
    """Tests for ModelConfigParser class."""
    
    def test_load_config_file_success(self, tmp_path):
        """Test loading valid config file."""
        from utils.model_config_parser import ModelConfigParser
        
        config_file = tmp_path / "model.json"
        config_file.write_text(json.dumps({
            "temperature": 0.7,
            "max_tokens": 2000
        }))
        
        config = ModelConfigParser.load_config_file(config_file)
        assert config["temperature"] == 0.7
        assert config["max_tokens"] == 2000
    
    def test_load_config_file_not_found(self):
        """Test error when config file doesn't exist."""
        from utils.model_config_parser import ModelConfigParser, ModelConfigError
        
        with pytest.raises(ModelConfigError, match="not found"):
            ModelConfigParser.load_config_file("/nonexistent/path/config.json")
    
    def test_load_config_file_not_a_file(self, tmp_path):
        """Test error when path is directory not file."""
        from utils.model_config_parser import ModelConfigParser, ModelConfigError
        
        directory = tmp_path / "config_dir"
        directory.mkdir()
        
        with pytest.raises(ModelConfigError, match="not a file"):
            ModelConfigParser.load_config_file(directory)
    
    def test_load_config_file_invalid_json(self, tmp_path):
        """Test error on invalid JSON."""
        from utils.model_config_parser import ModelConfigParser
        
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{ invalid json }")
        
        # Should raise some exception (either ModelConfigError or JSON decode error)
        with pytest.raises(Exception):
            ModelConfigParser.load_config_file(config_file)
    
    def test_load_config_file_non_dict(self, tmp_path):
        """Test error when file contains non-dictionary."""
        from utils.model_config_parser import ModelConfigParser, ModelConfigError
        
        config_file = tmp_path / "list.json"
        config_file.write_text('["item1", "item2"]')
        
        with pytest.raises(ModelConfigError, match="must contain.*object"):
            ModelConfigParser.load_config_file(config_file)
    
    def test_parse_property_override_simple(self):
        """Test parsing simple property override."""
        from utils.model_config_parser import ModelConfigParser
        
        result = ModelConfigParser.parse_property_override("temperature:0.8")
        assert result == ("temperature", 0.8)
    
    def test_parse_property_override_nested(self):
        """Test parsing nested property override."""
        from utils.model_config_parser import ModelConfigParser
        
        result = ModelConfigParser.parse_property_override("model.temperature:0.8")
        assert result == ("model.temperature", 0.8)
    
    def test_parse_property_override_string_value(self):
        """Test parsing string values."""
        from utils.model_config_parser import ModelConfigParser
        
        result = ModelConfigParser.parse_property_override("name:gpt-4o")
        assert result == ("name", "gpt-4o")
    
    def test_parse_property_override_int_value(self):
        """Test parsing integer values."""
        from utils.model_config_parser import ModelConfigParser
        
        result = ModelConfigParser.parse_property_override("max_tokens:1000")
        assert result == ("max_tokens", 1000)
    
    def test_parse_property_override_float_value(self):
        """Test parsing float values."""
        from utils.model_config_parser import ModelConfigParser
        
        result = ModelConfigParser.parse_property_override("temperature:0.7")
        assert result == ("temperature", 0.7)
    
    def test_parse_property_override_bool_true(self):
        """Test parsing boolean true values."""
        from utils.model_config_parser import ModelConfigParser
        
        result = ModelConfigParser.parse_property_override("enabled:true")
        assert result == ("enabled", True)
        
        result = ModelConfigParser.parse_property_override("enabled:True")
        assert result == ("enabled", True)
    
    def test_parse_property_override_bool_false(self):
        """Test parsing boolean false values."""
        from utils.model_config_parser import ModelConfigParser
        
        result = ModelConfigParser.parse_property_override("enabled:false")
        assert result == ("enabled", False)
        
        result = ModelConfigParser.parse_property_override("enabled:False")
        assert result == ("enabled", False)
    
    def test_parse_property_override_invalid_format(self):
        """Test error on invalid override format."""
        from utils.model_config_parser import ModelConfigParser, ModelConfigError
        
        with pytest.raises(ModelConfigError, match="Invalid.*format"):
            ModelConfigParser.parse_property_override("no_colon_here")
    
    def test_parse_property_override_empty_key(self):
        """Test error on empty key."""
        from utils.model_config_parser import ModelConfigParser, ModelConfigError
        
        with pytest.raises(ModelConfigError):
            ModelConfigParser.parse_property_override(":value")
    
    def test_apply_property_override_simple(self):
        """Test applying simple property override."""
        from utils.model_config_parser import ModelConfigParser
        
        config = {"temperature": 0.5}
        ModelConfigParser.apply_property_override(config, "temperature", 0.9)
        assert config["temperature"] == 0.9
    
    def test_apply_property_override_nested(self):
        """Test applying nested property override."""
        from utils.model_config_parser import ModelConfigParser
        
        config = {"model": {"temperature": 0.5}}
        ModelConfigParser.apply_property_override(config, "model.temperature", 0.9)
        assert config["model"]["temperature"] == 0.9
    
    def test_apply_property_override_creates_nested(self):
        """Test that nested paths are created if they don't exist."""
        from utils.model_config_parser import ModelConfigParser
        
        config = {}
        ModelConfigParser.apply_property_override(config, "model.temperature", 0.9)
        assert config["model"]["temperature"] == 0.9
    
    def test_apply_property_override_deep_nesting(self):
        """Test deeply nested property paths."""
        from utils.model_config_parser import ModelConfigParser
        
        config = {}
        ModelConfigParser.apply_property_override(config, "a.b.c.d", "value")
        assert config["a"]["b"]["c"]["d"] == "value"
    
    def test_merge_configs_multiple(self):
        """Test merging config with multiple overrides."""
        from utils.model_config_parser import ModelConfigParser
        
        config = {"temperature": 0.5}
        overrides = [
            "temperature:0.9",
            "max_tokens:2000",
            "model.name:gpt-4o"
        ]
        
        result = ModelConfigParser.merge_configs(config, overrides)
        assert result["temperature"] == 0.9
        assert result["max_tokens"] == 2000
        assert result["model"]["name"] == "gpt-4o"
    
    def test_merge_configs_empty_list(self):
        """Test that empty override list returns copy of config."""
        from utils.model_config_parser import ModelConfigParser
        
        config = {"temperature": 0.5}
        result = ModelConfigParser.merge_configs(config, [])
        assert result == config
        # Ensure it's a copy
        result["temperature"] = 0.9
        assert config["temperature"] == 0.5
    
    def test_parse_config_with_overrides(self, tmp_path):
        """Test parse_model_config utility function."""
        from utils.model_config_parser import parse_model_config
        
        config_file = tmp_path / "model.json"
        config_file.write_text(json.dumps({
            "temperature": 0.5,
            "max_tokens": 1000
        }))
        
        result = parse_model_config(
            str(config_file),
            ["temperature:0.9", "top_p:0.95"]
        )
        
        assert result["temperature"] == 0.9  # Overridden
        assert result["max_tokens"] == 1000  # From file
        assert result["top_p"] == 0.95  # New from override
    
    def test_parse_config_no_file(self):
        """Test parsing with overrides only (no file)."""
        from utils.model_config_parser import parse_model_config
        
        result = parse_model_config(None, ["temperature:0.7"])
        assert result["temperature"] == 0.7
    
    def test_parse_config_no_overrides(self, tmp_path):
        """Test parsing file only (no overrides)."""
        from utils.model_config_parser import parse_model_config
        
        config_file = tmp_path / "model.json"
        config_file.write_text(json.dumps({"temperature": 0.5}))
        
        result = parse_model_config(str(config_file), [])
        assert result["temperature"] == 0.5


@pytest.mark.unit
class TestTypeInference:
    """Tests for automatic type inference in overrides."""
    
    def test_infer_int(self):
        """Test integer type inference."""
        from utils.model_config_parser import ModelConfigParser
        
        _, value = ModelConfigParser.parse_property_override("count:42")
        assert isinstance(value, int)
        assert value == 42
    
    def test_infer_float(self):
        """Test float type inference."""
        from utils.model_config_parser import ModelConfigParser
        
        _, value = ModelConfigParser.parse_property_override("temp:0.7")
        assert isinstance(value, float)
        assert value == 0.7
    
    def test_infer_bool(self):
        """Test boolean type inference."""
        from utils.model_config_parser import ModelConfigParser
        
        _, value = ModelConfigParser.parse_property_override("enabled:true")
        assert isinstance(value, bool)
        assert value is True
    
    def test_infer_string(self):
        """Test string type (default)."""
        from utils.model_config_parser import ModelConfigParser
        
        _, value = ModelConfigParser.parse_property_override("name:test-model")
        assert isinstance(value, str)
        assert value == "test-model"
