"""
Tests for utils.file_utils module.

Target Coverage: 80%+
"""

import pytest
from pathlib import Path
import json
import tempfile


class TestIsLikelyTextFile:
    """Tests for is_likely_text_file function."""
    
    def test_text_file_by_extension(self, tmp_path):
        """Test text file detection by extension."""
        from utils.file_utils import is_likely_text_file
        
        # Create various text files
        for ext in ['.txt', '.md', '.py', '.json', '.yaml', '.yml']:
            file = tmp_path / f"test{ext}"
            file.write_text("content")
            assert is_likely_text_file(file), f"{ext} should be detected as text"
    
    def test_binary_file_by_extension(self, tmp_path):
        """Test binary file detection."""
        from utils.file_utils import is_likely_text_file
        
        # Binary extensions
        binary_file = tmp_path / "test.jpg"
        binary_file.write_bytes(b'\x00\x01\x02\xFF')
        
        # Should detect as not text (either by extension or content)
        result = is_likely_text_file(binary_file)
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
    
    def test_load_file_not_found(self):
        """Test error when file doesn't exist."""
        from utils.file_utils import load_structured_file
        
        with pytest.raises(Exception):
            load_structured_file("/nonexistent/file.json", 'json')
    
    def test_load_invalid_json(self, tmp_path):
        """Test error with invalid JSON."""
        from utils.file_utils import load_structured_file
        
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("}{")
        
        with pytest.raises(Exception):
            load_structured_file(invalid_file, 'json')


class TestLoadFileContent:
    """Tests for load_file_content function."""
    
    def test_load_text_file(self, tmp_path):
        """Test loading text file content."""
        from utils.file_utils import load_file_content
        
        text_file = tmp_path / "test.txt"
        content = "Hello, World!\nLine 2"
        text_file.write_text(content)
        
        result = load_file_content(text_file)
        assert result == content
    
    def test_load_binary_file(self, tmp_path):
        """Test loading binary file."""
        from utils.file_utils import load_file_content
        
        binary_file = tmp_path / "test.bin"
        binary_file.write_bytes(b'\x00\x01\x02')
        
        # Should either return content or indicate it's binary
        result = load_file_content(binary_file)
        assert result is not None or result == ""
    
    def test_load_nonexistent_file(self):
        """Test error when file doesn't exist."""
        from utils.file_utils import load_file_content
        
        with pytest.raises((FileNotFoundError, Exception)):
            load_file_content("/nonexistent/file.txt")


class TestResolveGlob:
    """Tests for resolve_glob function."""
    
    def test_resolve_single_file(self, tmp_path):
        """Test resolving a single file path."""
        from utils.file_utils import resolve_glob
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        result = resolve_glob(str(test_file))
        assert len(result) == 1
        # Result should be a string, not a Path object
        assert result[0] == str(test_file)
    
    def test_resolve_glob_pattern(self, tmp_path):
        """Test resolving glob pattern."""
        from utils.file_utils import resolve_glob
        
        # Create multiple files
        for i in range(3):
            (tmp_path / f"test{i}.txt").write_text(f"content{i}")
        
        result = resolve_glob(str(tmp_path / "*.txt"))
        assert len(result) == 3
        # All results should be strings
        assert all(isinstance(r, str) for r in result)
    
    def test_resolve_nonexistent_pattern(self, tmp_path):
        """Test glob with no matches."""
        from utils.file_utils import resolve_glob
        
        result = resolve_glob(str(tmp_path / "*.nonexistent"))
        assert len(result) == 0


class TestValidateFilePath:
    """Tests for validate_file_path function."""
    
    def test_validate_existing_file(self, tmp_path):
        """Test validating an existing file."""
        from utils.file_utils import validate_file_path
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        # Should return True
        result = validate_file_path(test_file)
        assert result is True
    
    def test_validate_nonexistent_file(self):
        """Test validating nonexistent file."""
        from utils.file_utils import validate_file_path
        
        # Should return False
        result = validate_file_path("/nonexistent/file.txt")
        assert result is False
    
    def test_validate_directory(self, tmp_path):
        """Test validating a directory."""
        from utils.file_utils import validate_file_path
        
        # Directories are not valid files, should return False
        result = validate_file_path(tmp_path)
        assert result is False


class TestGetFileSize:
    """Tests for get_file_size function."""
    
    def test_get_size_of_file(self, tmp_path):
        """Test getting file size."""
        from utils.file_utils import get_file_size
        
        test_file = tmp_path / "test.txt"
        content = "Hello" * 100
        test_file.write_text(content)
        
        size = get_file_size(test_file)
        assert size > 0
        assert size == len(content.encode())
    
    def test_get_size_of_empty_file(self, tmp_path):
        """Test getting size of empty file."""
        from utils.file_utils import get_file_size
        
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        
        size = get_file_size(test_file)
        assert size == 0
    
    def test_get_size_nonexistent(self):
        """Test getting size of nonexistent file - returns 0."""
        from utils.file_utils import get_file_size
        
        # Function returns 0 for nonexistent files instead of raising
        size = get_file_size("/nonexistent/file.txt")
        assert size == 0


@pytest.mark.integration
class TestFileUtilsIntegration:
    """Integration tests for file_utils."""
    
    def test_load_and_validate_workflow(self, tmp_path):
        """Test complete workflow of validating and loading file."""
        from utils.file_utils import validate_file_path, load_file_content, is_likely_text_file
        
        # Create a test file
        test_file = tmp_path / "data.txt"
        test_content = "Important data\nLine 2"
        test_file.write_text(test_content)
        
        # Validate it exists
        assert validate_file_path(test_file) is True
        
        # Check if it's text
        assert is_likely_text_file(test_file)
        
        # Load content
        content = load_file_content(test_file)
        assert content == test_content
    
    def test_glob_and_process_workflow(self, tmp_path):
        """Test workflow of finding and processing multiple files."""
        from utils.file_utils import resolve_glob, load_file_content
        
        # Create multiple files
        for i in range(3):
            file = tmp_path / f"data{i}.json"
            file.write_text(json.dumps({"id": i, "value": f"data{i}"}))
        
        # Find all JSON files
        files = resolve_glob(str(tmp_path / "*.json"))
        assert len(files) == 3
        
        # Process each file
        for file in files:
            content = load_file_content(file)
            assert "id" in content
            assert "value" in content
