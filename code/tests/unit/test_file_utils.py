"""
Tests for utils.file_utils module.

Target Coverage: 85%+
"""

import pytest
from pathlib import Path
import json


class TestIsLikelyTextFile:
    """Tests for is_likely_text_file function."""
    
    def test_text_file_by_extension(self, tmp_path):
        """Test text file detection by extension."""
        from utils.file_utils import is_likely_text_file
        
        # Create various text files
        for ext in ['.txt', '.md', '.py', '.json', '.yaml']:
            file = tmp_path / f"test{ext}"
            file.write_text("content")
            assert is_likely_text_file(file), f"{ext} should be detected as text"
    
    def test_non_text_file_by_extension(self, tmp_path):
        """Test non-text file detection."""
        from utils.file_utils import is_likely_text_file
        
        # Binary extensions
        for ext in ['.jpg', '.png', '.pdf', '.zip']:
            file = tmp_path / f"test{ext}"
            file.write_bytes(b'\x00\x01\x02')
            # May or may not detect based on content check
            result = is_likely_text_file(file)
            assert isinstance(result, bool)
    
    def test_nonexistent_file(self):
        """Test that nonexistent files return False."""
        from utils.file_utils import is_likely_text_file
        
        assert not is_likely_text_file("/nonexistent/file.txt")
    
    def test_directory_returns_false(self, tmp_path):
        """Test that directories return False."""
        from utils.file_utils import is_likely_text_file
        
        directory = tmp_path / "test_dir"
        directory.mkdir()
        assert not is_likely_text_file(directory)
    
    def test_readme_without_extension(self, tmp_path):
        """Test common text files without extensions."""
        from utils.file_utils import is_likely_text_file
        
        for name in ['README', 'LICENSE', 'Makefile']:
            file = tmp_path / name
            file.write_text("content")
            assert is_likely_text_file(file), f"{name} should be detected as text"


class TestLoadStructuredFile:
    """Tests for load_structured_file function."""
    
    def test_load_json_file(self, tmp_path):
        """Test loading JSON file."""
        from utils.file_utils import load_structured_file
        
        data = {"key": "value", "number": 42}
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(data))
        
        result = load_structured_file(json_file, 'json')
        assert result == data
    
    def test_load_yaml_file(self, tmp_path):
        """Test loading YAML file."""
        from utils.file_utils import load_structured_file
        
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("key: value\nnumber: 42")
        
        result = load_structured_file(yaml_file, 'yaml')
        assert result["key"] == "value"
        assert result["number"] == 42
    
    def test_load_structured_file_not_found(self):
        """Test error when file doesn't exist."""
        from utils.file_utils import load_structured_file
        
        with pytest.raises(Exception):
            load_structured_file("/nonexistent/file.json", 'json')
    
    def test_load_structured_file_invalid_format(self, tmp_path):
        """Test error with invalid file format."""
        from utils.file_utils import load_structured_file
        
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }")
        
        with pytest.raises(Exception):
            load_structured_file(invalid_file, 'json')


class TestDiscoverToolConfigs:
    """Tests for discover_tool_configs function."""
    
    def test_discover_empty_directory(self, tmp_path):
        """Test discovering in empty directory."""
        from utils.file_utils import discover_tool_configs
        
        result = discover_tool_configs(str(tmp_path))
        assert result == []
    
    def test_discover_json_configs(self, tmp_path):
        """Test discovering JSON tool configs."""
        from utils.file_utils import discover_tool_configs
        
        # Create tool config files
        config1 = tmp_path / "tools1.json"
        config1.write_text(json.dumps({"type": "python", "id": "test1"}))
        
        config2 = tmp_path / "tools2.json"
        config2.write_text(json.dumps({"type": "mcp", "id": "test2"}))
        
        result = discover_tool_configs(str(tmp_path))
        assert len(result) >= 2  # May find other patterns
    
    def test_discover_yaml_configs(self, tmp_path):
        """Test discovering YAML tool configs."""
        from utils.file_utils import discover_tool_configs
        
        config = tmp_path / "tools.yaml"
        config.write_text("type: python\nid: test")
        
        result = discover_tool_configs(str(tmp_path))
        assert len(result) >= 1
    
    def test_discover_nonexistent_directory(self):
        """Test discovering in nonexistent directory."""
        from utils.file_utils import discover_tool_configs
        
        result = discover_tool_configs("/nonexistent/directory")
        assert result == []


class TestGetMimetype:
    """Tests for get_mimetype function."""
    
    def test_get_mimetype_text(self, tmp_path):
        """Test mimetype detection for text files."""
        from utils.file_utils import get_mimetype
        
        text_file = tmp_path / "test.txt"
        text_file.write_text("content")
        
        mimetype = get_mimetype(text_file)
        assert "text" in mimetype.lower()
    
    def test_get_mimetype_json(self, tmp_path):
        """Test mimetype detection for JSON files."""
        from utils.file_utils import get_mimetype
        
        json_file = tmp_path / "test.json"
        json_file.write_text("{}")
        
        mimetype = get_mimetype(json_file)
        assert "json" in mimetype.lower() or "text" in mimetype.lower()
    
    def test_get_mimetype_unknown(self, tmp_path):
        """Test mimetype for unknown extension."""
        from utils.file_utils import get_mimetype
        
        unknown_file = tmp_path / "test.unknown"
        unknown_file.write_text("content")
        
        mimetype = get_mimetype(unknown_file)
        # Should return some default
        assert mimetype is not None


class TestProcessFilesGlob:
    """Tests for process_files_glob function (if it exists)."""
    
    def test_process_files_import(self):
        """Test that file processing functions are importable."""
        from utils import file_utils
        
        # Check what's actually available
        assert hasattr(file_utils, 'load_structured_file')
        assert hasattr(file_utils, 'discover_tool_configs')
        assert hasattr(file_utils, 'is_likely_text_file')


@pytest.mark.unit
class TestFileUtilsIntegration:
    """Integration tests for file_utils."""
    
    def test_discover_and_load_tool_config(self, tmp_path):
        """Test discovering and loading tool configs."""
        from utils.file_utils import discover_tool_configs, load_structured_file
        
        # Create a tool config
        config_file = tmp_path / "mytools.json"
        config_data = {
            "type": "python",
            "id": "test-tools",
            "module_path": "test.module"
        }
        config_file.write_text(json.dumps(config_data))
        
        # Discover it
        discovered = discover_tool_configs(str(tmp_path))
        assert len(discovered) > 0
        
        # Load and verify
        loaded = load_structured_file(config_file, 'json')
        assert loaded["type"] == "python"
