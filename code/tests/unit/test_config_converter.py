"""
Tests for adapters.strands_factory.config_converter module.

Target Coverage: 90%+
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch


class TestYacbaToStrandsConfigConverter:
    """Tests for YacbaToStrandsConfigConverter class."""

    def test_init(self, minimal_yacba_config):
        """Test converter initialization."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter

        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)
        assert converter.yacba_config == minimal_yacba_config

    def test_convert_minimal_config(self, minimal_yacba_config):
        """Test conversion of minimal configuration."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter

        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)
        result = converter.convert()

        # Check basic fields
        assert result.model == "gpt-4o"
        assert result.conversation_manager_type == "sliding_window"
        assert result.sliding_window_size == 40
        assert result.should_truncate_results is True

    def test_convert_full_config(self, tmp_path):
        """Test conversion of fully populated configuration."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter
        from config import YacbaConfig

        # Create actual file that strands will validate
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        full_config = YacbaConfig(
            model_string="anthropic:claude-3-5-sonnet-20241022",
            tool_config_paths=[],
            startup_files_content=None,
            prompt_source="cli",
            system_prompt="You are a test assistant",
            emulate_system_prompt=False,
            model_config=None,
            summarization_model_config=None,
            files_to_upload=[(str(test_file), "text/plain")],
            max_files=20,
            tool_configs_dir=None,
            tool_discovery_result=None,
            session_name="test_session",
            agent_id="test_agent",
            conversation_manager_type="summarizing",
            sliding_window_size=50,
            preserve_recent_messages=15,
            summary_ratio=0.25,
            summarization_model="gpt-3.5-turbo",
            custom_summarization_prompt="Summarize this",
            should_truncate_results=False,
            headless=True,
            initial_message="Test message",
            show_tool_use=True,
            cli_prompt="Test> ",
            response_prefix="AI: ",
        )

        converter = YacbaToStrandsConfigConverter(full_config)
        result = converter.convert()

        # Check all major fields
        assert result.model == "anthropic:claude-3-5-sonnet-20241022"
        assert result.system_prompt == "You are a test assistant"
        assert result.initial_message == "Test message"
        assert result.session_id == "test_session"
        assert result.conversation_manager_type == "summarizing"
        assert result.sliding_window_size == 50
        assert result.preserve_recent_messages == 15
        assert result.summary_ratio == 0.25
        assert result.summarization_model == "gpt-3.5-turbo"
        assert result.show_tool_use is True

    def test_convert_tool_configs_empty(self, minimal_yacba_config):
        """Test tool config conversion with no tools."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter

        minimal_yacba_config.tool_config_paths = []
        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)

        result = converter._convert_tool_configs()
        assert result == []

    def test_convert_tool_configs_with_paths(self, minimal_yacba_config):
        """Test tool config conversion with paths."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter

        minimal_yacba_config.tool_config_paths = ["./tools", "/etc/tools"]
        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)

        result = converter._convert_tool_configs()
        assert len(result) == 2
        assert all(isinstance(p, Path) for p in result)
        assert result[0] == Path("./tools")
        assert result[1] == Path("/etc/tools")

    def test_convert_file_uploads_empty(self, minimal_yacba_config):
        """Test file upload conversion with no files."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter

        minimal_yacba_config.files_to_upload = []
        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)

        result = converter._convert_file_uploads()
        assert result == []

    def test_convert_file_uploads_tuple_format(self, minimal_yacba_config, tmp_path):
        """Test file upload conversion with (path, mimetype) tuples."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter

        # Create actual files
        file1 = tmp_path / "test.txt"
        file1.write_text("test")
        file2 = tmp_path / "data.json"
        file2.write_text("{}")

        minimal_yacba_config.files_to_upload = [
            (str(file1), "text/plain"),
            (str(file2), "application/json"),
        ]
        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)

        result = converter._convert_file_uploads()
        assert len(result) == 2
        assert result[0] == (Path(str(file1)), "text/plain")
        assert result[1] == (Path(str(file2)), "application/json")

    def test_convert_file_uploads_dict_format(self, minimal_yacba_config, tmp_path):
        """Test file upload conversion with dict format."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter

        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        minimal_yacba_config.files_to_upload = [
            {"path": str(test_file), "mimetype": "text/plain"}
        ]
        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)

        result = converter._convert_file_uploads()
        assert len(result) == 1
        assert result[0] == (Path(str(test_file)), "text/plain")

    def test_convert_file_uploads_path_only(self, minimal_yacba_config, tmp_path):
        """Test file upload conversion with path only (no mimetype)."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter

        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        minimal_yacba_config.files_to_upload = [str(test_file)]
        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)

        result = converter._convert_file_uploads()
        assert len(result) == 1
        assert result[0] == (Path(str(test_file)), None)

    def test_get_sessions_home_no_session(self, minimal_yacba_config):
        """Test sessions home when no session is configured."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter

        minimal_yacba_config.session_name = None
        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)

        result = converter._get_sessions_home()
        assert result is None

    def test_get_sessions_home_with_session(self, minimal_yacba_config):
        """Test sessions home when session is configured."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter

        minimal_yacba_config.session_name = "test_session"
        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)

        result = converter._get_sessions_home()
        assert result is not None
        assert isinstance(result, Path)
        assert ".yacba" in str(result)
        assert "sessions" in str(result)

    def test_build_initial_message_none(self, minimal_yacba_config):
        """Test building initial message when none provided."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter

        minimal_yacba_config.initial_message = None
        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)

        result = converter._build_initial_message()
        assert result is None

    def test_build_initial_message_provided(self, minimal_yacba_config):
        """Test building initial message when provided."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter

        minimal_yacba_config.initial_message = "Hello world"
        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)

        result = converter._build_initial_message()
        assert result == "Hello world"

    def test_convert_conversation_manager_type_null(self, minimal_yacba_config):
        """Test conversion of null conversation manager."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter

        minimal_yacba_config.conversation_manager_type = "null"
        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)

        result = converter._convert_conversation_manager_type()
        assert result == "null"

    def test_convert_conversation_manager_type_sliding_window(
        self, minimal_yacba_config
    ):
        """Test conversion of sliding_window conversation manager."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter

        minimal_yacba_config.conversation_manager_type = "sliding_window"
        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)

        result = converter._convert_conversation_manager_type()
        assert result == "sliding_window"

    def test_convert_conversation_manager_type_summarizing(self, minimal_yacba_config):
        """Test conversion of summarizing conversation manager."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter

        minimal_yacba_config.conversation_manager_type = "summarizing"
        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)

        result = converter._convert_conversation_manager_type()
        assert result == "summarizing"

    def test_convert_conversation_manager_type_invalid(self, minimal_yacba_config):
        """Test conversion with invalid conversation manager type."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter

        minimal_yacba_config.conversation_manager_type = "invalid_type"
        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)

        # Should default to sliding_window with warning
        result = converter._convert_conversation_manager_type()
        assert result == "sliding_window"


@pytest.mark.unit
class TestConfigConversionIntegration:
    """Integration tests for config conversion."""

    def test_minimal_conversion_pipeline(self, minimal_yacba_config):
        """Test conversion of minimal config to AgentFactoryConfig."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter
        from strands_agent_factory import AgentFactoryConfig

        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)
        result = converter.convert()

        # Verify result is correct type
        assert isinstance(result, AgentFactoryConfig)

        # Verify key fields
        assert result.model == "gpt-4o"
        assert result.conversation_manager_type == "sliding_window"

    def test_conversion_with_tools(self, minimal_yacba_config, tmp_path):
        """Test conversion with tool configuration."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter
        import json

        # Create actual tool config files
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        tool1 = tools_dir / "tool1.json"
        tool1.write_text(json.dumps({"type": "python", "id": "test"}))

        more_tools_dir = tmp_path / "more_tools"
        more_tools_dir.mkdir()
        tool2 = more_tools_dir / "tool2.json"
        tool2.write_text(json.dumps({"type": "mcp", "id": "test2"}))

        minimal_yacba_config.tool_config_paths = [str(tool1), str(tool2)]
        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)
        result = converter.convert()

        assert len(result.tool_config_paths) == 2
        assert all(isinstance(p, Path) for p in result.tool_config_paths)

    def test_output_printer_interactive_mode(self, minimal_yacba_config):
        """Test that output_printer uses auto_printer in interactive mode."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter

        minimal_yacba_config.headless = False
        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)
        result = converter.convert()

        # Should use auto_printer (not the plain print function)
        assert result.output_printer != print

    def test_output_printer_headless_mode(self, minimal_yacba_config):
        """Test that output_printer uses plain print in headless mode."""
        from adapters.strands_factory import YacbaToStrandsConfigConverter

        minimal_yacba_config.headless = True
        converter = YacbaToStrandsConfigConverter(minimal_yacba_config)
        result = converter.convert()

        # Should use plain print function in headless mode
        assert result.output_printer == print
