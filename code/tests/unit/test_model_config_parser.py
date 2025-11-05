"""
Tests for utils.model_config_parser module.

Target Coverage: 75%+
"""

import pytest
from pathlib import Path
import json


class TestModelConfigParser:
    """Tests for ModelConfigParser class."""
    
    def test_load_config_file_json(self, tmp_path):
        """Test loading JSON config file."""
        from utils.model_config_parser import ModelConfigParser
        
        config_file = tmp_path / "config.json"
        config_data = {
            "model": "gpt-4o",
            "temperature": 0.7
        }
        config_file.write_text(json.dumps(config_data))
        
        result = ModelConfigParser.load_config_file(config_file)
        assert result == config_data
    
    def test_load_config_file_yaml(self, tmp_path):
        """Test loading YAML config file."""
        from utils.model_config_parser import ModelConfigParser
        
        config_file = tmp_path / "config.yaml"
        config_file.write_text("model: gpt-4o\ntemperature: 0.7")
        
        result = ModelConfigParser.load_config_file(config_file)
        assert result["model"] == "gpt-4o"
        assert result["temperature"] == 0.7
    
    def test_load_config_file_not_found(self):
        """Test error when file doesn't exist."""
        from utils.model_config_parser import ModelConfigParser, ModelConfigError
        
        with pytest.raises(ModelConfigError, match="not found"):
            ModelConfigParser.load_config_file("/nonexistent/config.yaml")
    
    def test_load_config_file_invalid(self, tmp_path):
        """Test error on invalid file content."""
        from utils.model_config_parser import ModelConfigParser
        
        config_file = tmp_path / "invalid.json"
        # Use truly invalid content for both JSON and YAML
        config_file.write_text('}{')
        
        # Should raise ModelConfigError
        with pytest.raises(Exception):
            ModelConfigParser.load_config_file(config_file)
    
    def test_parse_property_override(self):
        """Test parsing property override strings."""
        from utils.model_config_parser import ModelConfigParser
        
        # Simple property
        path, value = ModelConfigParser.parse_property_override("temperature=0.7")
        assert path == "temperature"
        assert value == 0.7
        
        # Nested property
        path, value = ModelConfigParser.parse_property_override("model_config.temperature=0.9")
        assert path == "model_config.temperature"
        assert value == 0.9
    
    def test_merge_configs(self):
        """Test merging configurations."""
        from utils.model_config_parser import ModelConfigParser
        
        base = {"model": "gpt-4o", "temperature": 0.5}
        override = {"temperature": 0.9, "max_tokens": 1000}
        
        result = ModelConfigParser.merge_configs(base, override)
        assert result["model"] == "gpt-4o"  # From base
        assert result["temperature"] == 0.9  # Overridden
        assert result["max_tokens"] == 1000  # New
    
    def test_merge_configs_nested(self):
        """Test merging nested configurations."""
        from utils.model_config_parser import ModelConfigParser
        
        base = {"model_config": {"temperature": 0.5, "top_p": 1.0}}
        override = {"model_config": {"temperature": 0.9}}
        
        result = ModelConfigParser.merge_configs(base, override)
        assert result["model_config"]["temperature"] == 0.9  # Overridden
        assert result["model_config"]["top_p"] == 1.0  # Preserved
    
    def test_apply_property_override(self):
        """Test applying property overrides."""
        from utils.model_config_parser import ModelConfigParser
        
        config = {"model": "gpt-4o"}
        ModelConfigParser.apply_property_override(config, "temperature=0.7")
        
        assert config["temperature"] == 0.7
    
    def test_apply_property_override_nested(self):
        """Test applying nested property overrides."""
        from utils.model_config_parser import ModelConfigParser
        
        config = {"model_config": {}}
        ModelConfigParser.apply_property_override(config, "model_config.temperature=0.9")
        
        assert config["model_config"]["temperature"] == 0.9
    
    def test_validate_model_config(self):
        """Test model config validation."""
        from utils.model_config_parser import ModelConfigParser
        
        # Valid config
        valid_config = {"model": "gpt-4o", "temperature": 0.7}
        assert ModelConfigParser.validate_model_config(valid_config) is True
        
        # Invalid type
        invalid_config = "not a dict"
        assert ModelConfigParser.validate_model_config(invalid_config) is False
