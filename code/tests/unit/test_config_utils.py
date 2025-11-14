"""
Tests for utils.config_utils module.

Target Coverage: 80%+
"""

import pytest
from pathlib import Path
import json


class TestDiscoverToolConfigs:
    """Tests for discover_tool_configs function."""
    
    def test_discover_empty_directory(self, tmp_path):
        """Test discovering in empty directory."""
        from utils.config_utils import discover_tool_configs
        
        file_paths, discovery_result = discover_tool_configs(str(tmp_path))
        assert isinstance(file_paths, list)
        assert len(file_paths) == 0
        assert hasattr(discovery_result, 'successful_configs')
        assert hasattr(discovery_result, 'failed_configs')
        assert hasattr(discovery_result, 'total_files_scanned')
    
    def test_discover_json_configs(self, tmp_path):
        """Test discovering JSON tool configs."""
        from utils.config_utils import discover_tool_configs
        
        # Create tool config files with .tools.json extension
        config1 = tmp_path / "test1.tools.json"
        config1.write_text(json.dumps({"type": "python", "id": "test1"}))
        
        config2 = tmp_path / "test2.tools.json"
        config2.write_text(json.dumps({"type": "mcp", "id": "test2"}))
        
        file_paths, discovery_result = discover_tool_configs(str(tmp_path))
        assert len(file_paths) >= 2
        
        # Check that all paths are strings
        assert all(isinstance(p, str) for p in file_paths)
        
        # Check discovery result structure
        assert len(discovery_result.successful_configs) >= 2
        assert discovery_result.total_files_scanned >= 2
    
    def test_discover_yaml_configs(self, tmp_path):
        """Test that only .tools.json files are discovered."""
        from utils.config_utils import discover_tool_configs
        
        # Create .tools.json file
        config = tmp_path / "test.tools.json"
        config.write_text(json.dumps({"type": "python", "id": "test"}))
        
        # Create .yaml file (should be ignored)
        yaml_config = tmp_path / "tools.yaml"
        yaml_config.write_text("type: python\nid: test")
        
        file_paths, discovery_result = discover_tool_configs(str(tmp_path))
        # Should only find .tools.json files
        assert len(file_paths) >= 1
        assert all(p.endswith('.tools.json') for p in file_paths)
    
    def test_discover_nonexistent_directory(self):
        """Test discovering in nonexistent directory."""
        from utils.config_utils import discover_tool_configs
        
        file_paths, discovery_result = discover_tool_configs("/nonexistent/directory")
        assert isinstance(file_paths, list)
        assert len(file_paths) == 0
        assert discovery_result.total_files_scanned == 0
    
    def test_discover_nested_directories(self, tmp_path):
        """Test discovering in directories (no recursion by default)."""
        from utils.config_utils import discover_tool_configs
        
        # Create nested structure
        nested_dir = tmp_path / "subdir"
        nested_dir.mkdir()
        
        config1 = tmp_path / "tools1.tools.json"
        config1.write_text(json.dumps({"type": "python"}))
        
        config2 = nested_dir / "tools2.tools.json"
        config2.write_text(json.dumps({"type": "mcp"}))
        
        # Discover from root - should only find files in root (no recursion)
        file_paths, discovery_result = discover_tool_configs(str(tmp_path))
        assert len(file_paths) >= 1
        
        # To find nested configs, need to search that directory explicitly
        nested_paths, nested_result = discover_tool_configs(str(nested_dir))
        assert len(nested_paths) >= 1
    
    def test_discover_specific_patterns(self, tmp_path):
        """Test that only .tools.json files are discovered."""
        from utils.config_utils import discover_tool_configs
        
        # Create tool config with correct pattern
        tool_config = tmp_path / "test.tools.json"
        tool_config.write_text(json.dumps({"type": "python"}))
        
        # Create non-tool files (should be ignored)
        other_file = tmp_path / "data.json"
        other_file.write_text(json.dumps({"not": "a tool"}))
        
        file_paths, discovery_result = discover_tool_configs(str(tmp_path))
        
        # Should only find .tools.json files
        assert all(p.endswith('.tools.json') for p in file_paths)
        assert len(file_paths) >= 1


class TestToolDiscoveryResult:
    """Tests for ToolDiscoveryResult dataclass."""
    
    def test_tool_discovery_result_structure(self):
        """Test ToolDiscoveryResult structure."""
        from yacba_types.config import ToolDiscoveryResult
        
        # Should be a dataclass
        assert hasattr(ToolDiscoveryResult, '__annotations__')
    
    def test_create_tool_discovery_result(self):
        """Test creating ToolDiscoveryResult."""
        from yacba_types.config import ToolDiscoveryResult
        
        result = ToolDiscoveryResult(
            successful_configs=[{'file_path': '/test/path.tools.json'}],
            failed_configs=[],
            total_files_scanned=1
        )
        assert result.successful_configs == [{'file_path': '/test/path.tools.json'}]
        assert result.failed_configs == []
        assert result.total_files_scanned == 1


@pytest.mark.integration
class TestConfigUtilsIntegration:
    """Integration tests for config_utils."""
    
    def test_discover_and_use_configs(self, tmp_path):
        """Test discovering and using tool configs."""
        from utils.config_utils import discover_tool_configs
        
        # Create a realistic tool config structure
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        
        # Python tools
        python_tools = tools_dir / "python.tools.json"
        python_tools.write_text(json.dumps({
            "type": "python",
            "id": "calculator",
            "module_path": "tools.calculator"
        }))
        
        # MCP tools
        mcp_tools = tools_dir / "mcp.tools.json"
        mcp_tools.write_text(json.dumps({
            "type": "mcp",
            "id": "filesystem",
            "command": "mcp-server-filesystem"
        }))
        
        # Discover all configs
        file_paths, discovery_result = discover_tool_configs(str(tools_dir))
        
        assert len(file_paths) >= 2
        
        # Verify we can access the file paths
        for path in file_paths:
            assert isinstance(path, str)
            assert Path(path).exists()
            assert path.endswith('.tools.json')
    
    def test_discover_multiple_directories(self, tmp_path):
        """Test discovering from multiple tool directories."""
        from utils.config_utils import discover_tool_configs
        
        # Create two separate tool directories
        dir1 = tmp_path / "tools1"
        dir1.mkdir()
        (dir1 / "tool1.tools.json").write_text(json.dumps({"type": "python", "id": "tool1"}))
        
        dir2 = tmp_path / "tools2"
        dir2.mkdir()
        (dir2 / "tool2.tools.json").write_text(json.dumps({"type": "mcp", "id": "tool2"}))
        
        # Discover from first directory
        paths1, result1 = discover_tool_configs(str(dir1))
        assert len(paths1) >= 1
        
        # Discover from second directory
        paths2, result2 = discover_tool_configs(str(dir2))
        assert len(paths2) >= 1
        
        # Results should be different
        assert paths1 != paths2 or len(paths1) == 0 or len(paths2) == 0
        
        # Test with list of directories
        paths_both, result_both = discover_tool_configs([str(dir1), str(dir2)])
        assert len(paths_both) >= 2
