"""
Tests for adapters.cli.commands.info_commands module.

Tests for information display commands that work with the engine adapter.
"""

import pytest
import json
from unittest.mock import Mock, patch
from typing import List

from adapters.cli.commands.info_commands import InfoCommands
from cli.commands.base_command import CommandError


class TestInfoCommandsInit:
    """Test InfoCommands initialization."""

    def test_info_commands_initialization(self):
        """Test InfoCommands initialization."""
        mock_registry = Mock()
        mock_engine = Mock()
        info_cmd = InfoCommands(mock_registry, mock_engine)
        
        assert info_cmd.registry is mock_registry
        assert info_cmd.engine is mock_engine
        assert info_cmd._command_name == "info"


class TestInfoCommandsHandling:
    """Test info command handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = Mock()
        self.mock_engine = Mock()
        self.mock_engine.is_ready = True
        self.info_cmd = InfoCommands(self.mock_registry, self.mock_engine)

    @pytest.mark.asyncio
    async def test_handle_history_command(self):
        """Test handling /history command."""
        with patch.object(self.info_cmd, '_show_history') as mock_show_history:
            await self.info_cmd.handle_command('/history', [])
            mock_show_history.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_handle_tools_command(self):
        """Test handling /tools command."""
        with patch.object(self.info_cmd, '_list_tools') as mock_list_tools:
            await self.info_cmd.handle_command('/tools', [])
            mock_list_tools.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_handle_conversation_manager_command(self):
        """Test handling /conversation-manager command."""
        with patch.object(self.info_cmd, '_show_conversation_manager_info') as mock_show_cm:
            await self.info_cmd.handle_command('/conversation-manager', [])
            mock_show_cm.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_handle_conversation_stats_command(self):
        """Test handling /conversation-stats command."""
        with patch.object(self.info_cmd, '_show_conversation_stats') as mock_show_stats:
            await self.info_cmd.handle_command('/conversation-stats', [])
            mock_show_stats.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_handle_unknown_command(self):
        """Test handling unknown command."""
        with patch.object(self.info_cmd, 'print_error') as mock_print_error:
            await self.info_cmd.handle_command('/unknown', [])
            mock_print_error.assert_called_once_with("Unknown info command: /unknown")

    @pytest.mark.asyncio
    async def test_handle_command_error_exception(self):
        """Test handling CommandError exception."""
        with patch.object(self.info_cmd, '_show_history', side_effect=CommandError("Test error")):
            with patch.object(self.info_cmd, 'print_error') as mock_print_error:
                await self.info_cmd.handle_command('/history', [])
                mock_print_error.assert_called_once_with("Test error")

    @pytest.mark.asyncio
    async def test_handle_general_exception(self):
        """Test handling general exception."""
        with patch.object(self.info_cmd, '_show_history', side_effect=Exception("General error")):
            with patch.object(self.info_cmd, 'print_error') as mock_print_error:
                await self.info_cmd.handle_command('/history', [])
                mock_print_error.assert_called_once_with("Unexpected error in /history: General error")


class TestShowHistoryCommand:
    """Test the _show_history method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = Mock()
        self.mock_engine = Mock()
        self.mock_engine.is_ready = True
        self.info_cmd = InfoCommands(self.mock_registry, self.mock_engine)

    @pytest.mark.asyncio
    async def test_show_history_validation_failure(self):
        """Test history command with validation failure."""
        with patch.object(self.info_cmd, 'validate_args', return_value=False):
            await self.info_cmd._show_history(['invalid', 'args'])
            # Should return early without doing anything

    @pytest.mark.asyncio
    async def test_show_history_engine_not_ready(self):
        """Test history command when engine is not ready."""
        self.mock_engine.is_ready = False
        await self.info_cmd._show_history([])
        # Should return early without doing anything

    @pytest.mark.asyncio
    async def test_show_history_no_messages(self):
        """Test history command with no messages."""
        # Mock agent with no messages
        mock_agent = Mock()
        mock_agent.messages = None
        self.info_cmd.agent = mock_agent
        
        with patch.object(self.info_cmd, 'print_info') as mock_print_info:
            await self.info_cmd._show_history([])
            mock_print_info.assert_called_once_with("No conversation history available.")

    @pytest.mark.asyncio
    async def test_show_history_with_messages(self):
        """Test history command with messages."""
        # Mock agent with messages
        mock_agent = Mock()
        test_messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        mock_agent.messages = test_messages
        self.info_cmd.agent = mock_agent
        
        with patch.object(self.info_cmd, 'print_info') as mock_print_info:
            await self.info_cmd._show_history([])
            
            # Should print messages and history
            assert mock_print_info.call_count == 2
            mock_print_info.assert_any_call(": Current conversation history:")
            
            # Check that JSON was printed
            json_call = mock_print_info.call_args_list[1][0][0]
            parsed_json = json.loads(json_call)
            assert parsed_json == test_messages

    @pytest.mark.asyncio
    async def test_show_history_json_serialization_error(self):
        """Test history command with JSON serialization error."""
        # Mock agent with non-serializable messages
        mock_agent = Mock()
        mock_agent.messages = [{"key": object()}]  # Non-serializable object
        self.info_cmd.agent = mock_agent
        
        with patch.object(self.info_cmd, 'print_error') as mock_print_error:
            await self.info_cmd._show_history([])
            
            # Should print serialization error
            mock_print_error.assert_called()
            error_msg = mock_print_error.call_args[0][0]
            assert "Failed to serialize conversation history" in error_msg


class TestListToolsCommand:
    """Test the _list_tools method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = Mock()
        self.mock_engine = Mock()
        self.mock_engine.is_ready = True
        self.info_cmd = InfoCommands(self.mock_registry, self.mock_engine)

    @pytest.mark.asyncio
    async def test_list_tools_validation_failure(self):
        """Test tools command with validation failure."""
        with patch.object(self.info_cmd, 'validate_args', return_value=False):
            await self.info_cmd._list_tools(['invalid'])
            # Should return early

    @pytest.mark.asyncio
    async def test_list_tools_engine_not_ready(self):
        """Test tools command when engine not ready."""
        self.mock_engine.is_ready = False
        await self.info_cmd._list_tools([])
        # Should return early

    @pytest.mark.asyncio
    async def test_list_tools_no_tools(self):
        """Test tools command with no loaded tools."""
        self.mock_engine.loaded_tools = []
        
        with patch.object(self.info_cmd, 'print_info') as mock_print_info:
            await self.info_cmd._list_tools([])
            mock_print_info.assert_called_once_with("No tools are currently loaded.")

    @pytest.mark.asyncio
    async def test_list_tools_with_tools(self):
        """Test tools command with loaded tools."""
        # Mock tools
        mock_tool1 = Mock()
        mock_tool1.tool_spec = {"name": "test_tool1", "description": "Test tool 1"}
        mock_tool2 = Mock()
        mock_tool2.__name__ = "test_tool2"
        mock_tool2.__module__ = "test_module"
        
        self.mock_engine.loaded_tools = [mock_tool1, mock_tool2]
        
        with patch.object(self.info_cmd, 'print_info') as mock_print_info:
            with patch.object(self.info_cmd, '_get_tool_info', side_effect=["Tool 1 info", "Tool 2 info"]):
                await self.info_cmd._list_tools([])
                
                # Should print tool count and info for each tool
                mock_print_info.assert_any_call("Loaded tools (2):")
                mock_print_info.assert_any_call("Tool 1 info")
                mock_print_info.assert_any_call("Tool 2 info")


class TestGetToolInfo:
    """Test the _get_tool_info method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = Mock()
        self.mock_engine = Mock()
        self.info_cmd = InfoCommands(self.mock_registry, self.mock_engine)

    def test_get_tool_info_with_tool_spec(self):
        """Test tool info extraction with tool_spec."""
        mock_tool = Mock()
        mock_tool.tool_spec = {
            "name": "test_tool",
            "description": "A test tool for testing"
        }
        
        result = self.info_cmd._get_tool_info(mock_tool, 1)
        
        assert "1. test_tool" in result
        assert "A test tool for testing" in result

    def test_get_tool_info_with_function_name(self):
        """Test tool info extraction with function name."""
        mock_tool = Mock()
        mock_tool.__name__ = "test_function"
        mock_tool.__module__ = "test_module"
        delattr(mock_tool, 'tool_spec')  # Remove tool_spec
        
        result = self.info_cmd._get_tool_info(mock_tool, 2)
        
        assert "2. test_function" in result
        assert "Python (test_module)" in result

    def test_get_tool_info_with_class_name(self):
        """Test tool info extraction with class name."""
        mock_tool = Mock()
        mock_tool.__class__.__name__ = "TestClass"
        mock_tool.__class__.__module__ = "test_module"
        delattr(mock_tool, 'tool_spec')
        delattr(mock_tool, '__name__')
        
        result = self.info_cmd._get_tool_info(mock_tool, 3)
        
        assert "3. TestClass" in result
        assert "Class (test_module)" in result

    def test_get_tool_info_fallback(self):
        """Test tool info extraction fallback."""
        mock_tool = Mock()
        delattr(mock_tool, 'tool_spec')
        delattr(mock_tool, '__name__')
        mock_tool.__class__.__name__ = "Mock"
        mock_tool.__class__.__module__ = "unittest.mock"
        
        result = self.info_cmd._get_tool_info(mock_tool, 4)
        
        assert "4. Mock" in result
        assert "Class (unittest.mock)" in result

    def test_get_tool_info_long_description_truncation(self):
        """Test tool info with long description truncation."""
        mock_tool = Mock()
        long_description = "A" * 100  # Very long description
        mock_tool.tool_spec = {
            "name": "test_tool",
            "description": long_description
        }
        
        result = self.info_cmd._get_tool_info(mock_tool, 1)
        
        assert "..." in result  # Should be truncated
        assert len(result) < len(long_description) + 50  # Should be shorter


class TestConversationManagerInfo:
    """Test the _show_conversation_manager_info method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = Mock()
        self.mock_engine = Mock()
        self.mock_engine.is_ready = True
        self.info_cmd = InfoCommands(self.mock_registry, self.mock_engine)

    @pytest.mark.asyncio
    async def test_show_conversation_manager_sliding_window(self):
        """Test conversation manager info for sliding window."""
        self.mock_engine.config.conversation_manager_type = "sliding_window"
        self.mock_engine.config.sliding_window_size = 20
        self.mock_engine.config.should_truncate_results = True
        
        with patch.object(self.info_cmd, 'print_info') as mock_print_info:
            await self.info_cmd._show_conversation_manager_info([])
            
            mock_print_info.assert_any_call("Conversation Manager Configuration:")
            mock_print_info.assert_any_call("  Type: sliding_window")
            mock_print_info.assert_any_call("  Window Size: 20 messages")
            mock_print_info.assert_any_call("  Truncate Results: Yes")

    @pytest.mark.asyncio
    async def test_show_conversation_manager_summarizing(self):
        """Test conversation manager info for summarizing."""
        self.mock_engine.config.conversation_manager_type = "summarizing"
        self.mock_engine.config.summary_ratio = 0.4
        self.mock_engine.config.preserve_recent_messages = 15
        self.mock_engine.config.summarization_model = "test-model"
        self.mock_engine.config.custom_summarization_prompt = "Custom prompt"
        
        with patch.object(self.info_cmd, 'print_info') as mock_print_info:
            await self.info_cmd._show_conversation_manager_info([])
            
            mock_print_info.assert_any_call("  Type: summarizing")
            mock_print_info.assert_any_call("  Summary Ratio: 0.4 (40%)")
            mock_print_info.assert_any_call("  Preserve Recent: 15 messages")
            mock_print_info.assert_any_call("  Summarization Model: test-model")
            mock_print_info.assert_any_call("  Custom Prompt: Yes")

    @pytest.mark.asyncio
    async def test_show_conversation_manager_null(self):
        """Test conversation manager info for null type."""
        self.mock_engine.config.conversation_manager_type = "null"
        
        with patch.object(self.info_cmd, 'print_info') as mock_print_info:
            await self.info_cmd._show_conversation_manager_info([])
            
            mock_print_info.assert_any_call("  Type: null")
            mock_print_info.assert_any_call("  No conversation management (all history preserved)")


class TestGetCommandUsage:
    """Test the get_command_usage method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = Mock()
        self.mock_engine = Mock()
        self.info_cmd = InfoCommands(self.mock_registry, self.mock_engine)

    def test_get_command_usage_history(self):
        """Test usage for history command."""
        result = self.info_cmd.get_command_usage("/history")
        
        assert "/history" in result
        assert "Display the current conversation history as JSON" in result

    def test_get_command_usage_tools(self):
        """Test usage for tools command."""
        result = self.info_cmd.get_command_usage("/tools")
        
        assert "/tools" in result
        assert "List all currently loaded tools with details" in result

    def test_get_command_usage_conversation_manager(self):
        """Test usage for conversation-manager command."""
        result = self.info_cmd.get_command_usage("/conversation-manager")
        
        assert "/conversation-manager" in result
        assert "conversation manager configuration" in result

    def test_get_command_usage_conversation_stats(self):
        """Test usage for conversation-stats command."""
        result = self.info_cmd.get_command_usage("/conversation-stats")
        
        assert "/conversation-stats" in result
        assert "conversation statistics" in result

    def test_get_command_usage_unknown(self):
        """Test usage for unknown command."""
        with patch('adapters.cli.commands.adapted_commands.AdaptedCommands.get_command_usage', return_value="Unknown usage"):
            result = self.info_cmd.get_command_usage("/unknown")
            
            assert result == "Unknown usage"