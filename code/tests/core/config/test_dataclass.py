"""
Tests for core.config.dataclass module - WORKING VERSION.
"""

import pytest
from core.config.dataclass import YacbaConfig
from yacba_types.config import PythonToolConfig, MCPToolConfig
from yacba_types.content import Message


class TestYacbaConfigBasic:
    """Test basic YacbaConfig functionality."""

    def test_valid_config_creation(self):
        """Test creating a valid YacbaConfig instance."""
        config = YacbaConfig(
            model_string="litellm:gemini/gemini-1.5-flash",
            system_prompt="You are a helpful assistant.",
            prompt_source="command_line",
            tool_configs=[],
            startup_files_content=None
        )
        
        assert config.model_string == "litellm:gemini/gemini-1.5-flash"
        assert config.system_prompt == "You are a helpful assistant."
        assert config.prompt_source == "command_line"
        assert config.tool_configs == []
        assert config.startup_files_content is None

    def test_framework_name_property(self):
        """Test framework_name property extraction."""
        config = YacbaConfig(
            model_string="litellm:gemini/gemini-1.5-flash",
            system_prompt="Test prompt",
            prompt_source="test",
            tool_configs=[],
            startup_files_content=None
        )
        assert config.framework_name == "litellm"

    def test_model_name_property(self):
        """Test model_name property extraction."""
        config = YacbaConfig(
            model_string="litellm:gemini/gemini-1.5-flash",
            system_prompt="Test prompt", 
            prompt_source="test",
            tool_configs=[],
            startup_files_content=None
        )
        assert config.model_name == "gemini/gemini-1.5-flash"

    def test_different_framework_models(self):
        """Test framework and model extraction with different formats."""
        test_cases = [
            ("openai:gpt-4", "openai", "gpt-4"),
            ("anthropic:claude-3-sonnet", "anthropic", "claude-3-sonnet"),
            ("bedrock:anthropic.claude-3-sonnet-20240229-v1:0", "bedrock", "anthropic.claude-3-sonnet-20240229-v1:0")
        ]
        
        for model_string, expected_framework, expected_model in test_cases:
            config = YacbaConfig(
                model_string=model_string,
                system_prompt="Test",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None
            )
            assert config.framework_name == expected_framework
            assert config.model_name == expected_model


class TestYacbaConfigWithTools:
    """Test YacbaConfig with tool configurations - FIXED."""

    def test_with_python_tool_config(self):
        """Test YacbaConfig with Python tool configuration."""
        tool_configs = [
            PythonToolConfig(
                id="python_tool",
                name="Test Python Tool",
                description="A test Python tool",
                module_path="test.module"
            )
        ]
        
        config = YacbaConfig(
            model_string="gpt-4",
            system_prompt="Test prompt",
            prompt_source="test",
            tool_configs=tool_configs,
            startup_files_content=None
        )
        
        assert len(config.tool_configs) == 1
        assert config.tool_configs[0]["id"] == "python_tool"
        assert config.tool_configs[0]["name"] == "Test Python Tool"
        assert config.tool_configs[0]["module_path"] == "test.module"

    def test_with_mcp_tool_config(self):
        """Test YacbaConfig with MCP tool configuration."""
        tool_configs = [
            MCPToolConfig(
                id="mcp_tool",
                name="Test MCP Tool", 
                description="A test MCP tool",
                command="python",
                args=["-m", "test_server"]
            )
        ]
        
        config = YacbaConfig(
            model_string="gpt-4",
            system_prompt="Test prompt",
            prompt_source="test",
            tool_configs=tool_configs,
            startup_files_content=None
        )
        
        assert len(config.tool_configs) == 1
        assert config.tool_configs[0]["id"] == "mcp_tool"
        assert config.tool_configs[0]["command"] == "python"
        assert config.tool_configs[0]["args"] == ["-m", "test_server"]

    def test_with_mixed_tool_configs(self):
        """Test YacbaConfig with mixed tool configuration types."""
        tool_configs = [
            PythonToolConfig(
                id="python_tool",
                name="Python Tool",
                description="A Python tool",
                module_path="python.module"
            ),
            MCPToolConfig(
                id="mcp_tool",
                name="MCP Tool",
                description="An MCP tool", 
                command="mcp-server",
                args=["--port", "8080"]
            )
        ]
        
        config = YacbaConfig(
            model_string="openai:gpt-4",
            system_prompt="Test prompt",
            prompt_source="test",
            tool_configs=tool_configs,
            startup_files_content=None
        )
        
        assert len(config.tool_configs) == 2
        assert config.tool_configs[0]["id"] == "python_tool"
        assert config.tool_configs[1]["id"] == "mcp_tool"


class TestYacbaConfigWithContent:
    """Test YacbaConfig with startup content - FIXED."""

    def test_with_startup_files_content(self):
        """Test YacbaConfig with startup files content."""
        messages = [
            Message(
                role="user",
                content="Test message 1",
                timestamp="2024-01-01T00:00:00Z"
            ),
            Message(
                role="assistant", 
                content="Test response 1",
                timestamp="2024-01-01T00:01:00Z"
            )
        ]
        
        config = YacbaConfig(
            model_string="gpt-4",
            system_prompt="Test prompt",
            prompt_source="test",
            tool_configs=[],
            startup_files_content=messages
        )
        
        assert len(config.startup_files_content) == 2
        # Message is a TypedDict, accessed like a dict
        assert config.startup_files_content[0]["role"] == "user"
        assert config.startup_files_content[1]["role"] == "assistant"
        assert config.startup_files_content[0]["content"] == "Test message 1"


class TestYacbaConfigValidation:
    """Test YacbaConfig validation - FIXED to match actual behavior."""

    def test_headless_mode_requires_initial_message(self):
        """Test headless mode validation."""
        # This should fail - headless without initial_message
        with pytest.raises(ValueError, match="Headless mode requires an initial message"):
            YacbaConfig(
                model_string="gpt-4",
                system_prompt="Test",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None,
                headless=True  # This triggers validation
            )

    def test_headless_mode_with_initial_message_works(self):
        """Test headless mode with initial message works."""
        config = YacbaConfig(
            model_string="gpt-4",
            system_prompt="Test",
            prompt_source="test",
            tool_configs=[],
            startup_files_content=None,
            headless=True,
            initial_message="Start the conversation"
        )
        assert config.headless is True
        assert config.initial_message == "Start the conversation"

    def test_max_files_validation(self):
        """Test max_files validation."""
        # Test invalid max_files
        with pytest.raises(ValueError, match="max_files must be at least 1"):
            YacbaConfig(
                model_string="gpt-4",
                system_prompt="Test",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None,
                max_files=0
            )

        with pytest.raises(ValueError, match="max_files cannot exceed 1000"):
            YacbaConfig(
                model_string="gpt-4",
                system_prompt="Test",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None,
                max_files=1001
            )

    def test_empty_strings_are_allowed(self):
        """Test that empty strings are actually allowed - no validation."""
        config = YacbaConfig(
            model_string="",  # Empty string allowed
            system_prompt="",  # Empty string allowed
            prompt_source="",  # Empty string allowed
            tool_configs=[],
            startup_files_content=None
        )
        assert config.model_string == ""
        assert config.system_prompt == ""
        assert config.prompt_source == ""


class TestYacbaConfigEdgeCases:
    """Test YacbaConfig edge cases."""

    def test_complex_model_strings(self):
        """Test YacbaConfig with complex model string formats."""
        complex_models = [
            "bedrock:anthropic.claude-3-sonnet-20240229-v1:0",
            "azure:gpt-4-32k", 
            "litellm:gemini/gemini-1.5-flash-001"
        ]
        
        for model_string in complex_models:
            config = YacbaConfig(
                model_string=model_string,
                system_prompt="Test prompt",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None
            )
            assert config.model_string == model_string
            assert ":" in config.model_string

    def test_optional_fields_with_defaults(self):
        """Test YacbaConfig optional fields work correctly."""
        config = YacbaConfig(
            model_string="gpt-4",
            system_prompt="Test prompt",
            prompt_source="test", 
            tool_configs=[],
            startup_files_content=None,
            # Don't set headless=True to avoid validation
            max_files=50,
            show_tool_use=True,
            initial_message="Initial message for safety"
        )
        
        assert config.headless is False  # Default
        assert config.max_files == 50
        assert config.show_tool_use is True
        assert config.model_config == {}  # Default factory
        assert config.session_name is None  # Default None