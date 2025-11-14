"""
Tests for utils.model_config_parser module.

Target Coverage: 60%+
"""

import pytest
from pathlib import Path
import yaml


class TestModelConfigParser:
    """Tests for ModelConfigParser class."""
    
    def test_load_config_file_json(self, tmp_path):
        """Test loading model config from JSON file (via YAML parser)."""
        from utils.model_config_parser import ModelConfigParser
        
        config_file = tmp_path / "model_config.yaml"
        config_file.write_text(yaml.dump({"temperature": 0.7, "max_tokens": 1000}))
        
        result = ModelConfigParser.load_config_file(config_file)
        assert result["temperature"] == 0.7
        assert result["max_tokens"] == 1000
    
    def test_load_config_file_yaml(self, tmp_path):
        """Test loading model config from YAML file."""
        from utils.model_config_parser import ModelConfigParser
        
        config_file = tmp_path / "model_config.yaml"
        config_file.write_text("temperature: 0.8\nmax_tokens: 2000")
        
        result = ModelConfigParser.load_config_file(config_file)
        assert result["temperature"] == 0.8
        assert result["max_tokens"] == 2000
    
    def test_load_config_file_not_found(self):
        """Test error when config file doesn't exist."""
        from utils.model_config_parser import ModelConfigParser, ModelConfigError
        
        with pytest.raises(ModelConfigError):
            ModelConfigParser.load_config_file("/nonexistent/config.yaml")
    
    def test_load_config_file_invalid(self, tmp_path):
        """Test error with invalid YAML."""
        from utils.model_config_parser import ModelConfigParser, ModelConfigError
        
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        with pytest.raises(ModelConfigError):
            ModelConfigParser.load_config_file(config_file)
    
    def test_parse_property_override(self):
        """Test parsing property override with colon separator."""
        from utils.model_config_parser import ModelConfigParser
        
        # Correct format uses colon
        path, value = ModelConfigParser.parse_property_override("temperature: 0.7")
        assert path == "temperature"
        assert value == 0.7
    
    def test_merge_configs(self):
        """Test merging base config with overrides."""
        from utils.model_config_parser import ModelConfigParser
        
        base = {"temperature": 0.5, "max_tokens": 1000}
        overrides = ["temperature: 0.7"]
        
        result = ModelConfigParser.merge_configs(base, overrides)
        assert result["temperature"] == 0.7
        assert result["max_tokens"] == 1000
    
    def test_merge_configs_nested(self):
        """Test merging with nested property paths."""
        from utils.model_config_parser import ModelConfigParser
        
        base = {"response_format": {"type": "text"}, "temperature": 0.5}
        overrides = ["response_format.type: json"]
        
        result = ModelConfigParser.merge_configs(base, overrides)
        assert result["response_format"]["type"] == "json"
        assert result["temperature"] == 0.5
    
    def test_apply_property_override(self):
        """Test applying property override to config dict."""
        from utils.model_config_parser import ModelConfigParser
        
        config = {"temperature": 0.5}
        ModelConfigParser.apply_property_override(config, "temperature", 0.7)
        assert config["temperature"] == 0.7
    
    def test_apply_property_override_nested(self):
        """Test applying nested property override."""
        from utils.model_config_parser import ModelConfigParser
        
        config = {"response_format": {"type": "text"}}
        ModelConfigParser.apply_property_override(config, "response_format.type", "json")
        assert config["response_format"]["type"] == "json"
    
    def test_validate_model_config(self):
        """Test validating model config - returns None if valid."""
        from utils.model_config_parser import ModelConfigParser
        
        valid_config = {"model": "gpt-4o", "temperature": 0.7}
        # validate_model_config returns None on success
        result = ModelConfigParser.validate_model_config(valid_config)
        assert result is None


@pytest.mark.integration
class TestModelConfigParserIntegration:
    """Integration tests for model config parsing."""
    
    def test_load_and_override_workflow(self, tmp_path):
        """Test complete workflow of loading and overriding config."""
        from utils.model_config_parser import parse_model_config
        
        # Create config file
        config_file = tmp_path / "model.yaml"
        config_file.write_text(yaml.dump({
            "temperature": 0.5,
            "max_tokens": 1000,
            "response_format": {"type": "text"}
        }))
        
        # Load with overrides
        result = parse_model_config(
            config_file=str(config_file),
            overrides=[
                "temperature: 0.7",
                "response_format.type: json"
            ]
        )
        
        assert result["temperature"] == 0.7
        assert result["max_tokens"] == 1000
        assert result["response_format"]["type"] == "json"
    
    def test_overrides_only_workflow(self):
        """Test workflow with only overrides (no file)."""
        from utils.model_config_parser import parse_model_config
        
        result = parse_model_config(
            config_file=None,
            overrides=[
                "temperature: 0.9",
                "max_tokens: 500"
            ]
        )
        
        assert result["temperature"] == 0.9
        assert result["max_tokens"] == 500
    
    def test_type_inference(self):
        """Test automatic type inference in overrides."""
        from utils.model_config_parser import ModelConfigParser
        
        # Test various types
        test_cases = [
            ("temperature: 0.7", ("temperature", 0.7)),
            ("max_tokens: 1000", ("max_tokens", 1000)),
            ("enabled: true", ("enabled", True)),
            ("disabled: false", ("disabled", False)),
            ("name: 'test'", ("name", "test")),
            ("value: null", ("value", None)),
        ]
        
        for override, expected in test_cases:
            path, value = ModelConfigParser.parse_property_override(override)
            assert path == expected[0]
            assert value == expected[1]
            assert type(value) == type(expected[1])
    
    def test_nested_path_parsing(self):
        """Test parsing nested property paths."""
        from utils.model_config_parser import ModelConfigParser
        
        config = {}
        
        # Apply nested override
        ModelConfigParser.apply_property_override(
            config, 
            "response_format.type", 
            "json_object"
        )
        
        assert "response_format" in config
        assert config["response_format"]["type"] == "json_object"
    
    def test_array_indexing(self):
        """Test array indexing in property paths."""
        from utils.model_config_parser import ModelConfigParser
        
        config = {"items": [{"value": 1}, {"value": 2}]}
        
        # Override array element
        ModelConfigParser.apply_property_override(
            config,
            "items[0].value",
            10
        )
        
        assert config["items"][0]["value"] == 10
        assert config["items"][1]["value"] == 2
