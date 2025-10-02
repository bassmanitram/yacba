"""
Tests for cli.commands.base_command module.

Comprehensive testing of the abstract base command class and command system.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List

from cli.commands.base_command import (
    BaseCommand, 
    CommandError, 
    CommandValidationError, 
    CommandExecutionError
)


# Concrete implementation for testing
class TestableCommand(BaseCommand):
    """Concrete command implementation for testing."""
    
    def __init__(self, registry=None):
        self.registry = registry or Mock()
        super().__init__(self.registry)
        self.handle_command_called = False
        self.last_command = None
        self.last_args = None

    async def handle_command(self, command: str, args: List[str]) -> None:
        """Test implementation of handle_command."""
        self.handle_command_called = True
        self.last_command = command
        self.last_args = args


class TestBaseCommand:
    """Test BaseCommand abstract class functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = Mock()
        self.command = TestableCommand(self.mock_registry)

    def test_base_command_initialization(self):
        """Test BaseCommand initialization."""
        assert self.command.registry is self.mock_registry
        assert self.command._command_name == "testablecommand"

    def test_command_name_generation(self):
        """Test automatic command name generation."""
        # Test various class names
        class HelpCommand(BaseCommand):
            def __init__(self, registry):
                super().__init__(registry)
            async def handle_command(self, command: str, args: List[str]) -> None:
                pass

        class InfoCommands(BaseCommand):
            def __init__(self, registry):
                super().__init__(registry)
            async def handle_command(self, command: str, args: List[str]) -> None:
                pass

        help_cmd = HelpCommand(Mock())
        info_cmd = InfoCommands(Mock())

        assert help_cmd._command_name == "helpcommand"
        assert info_cmd._command_name == "info"

    def test_abstract_handle_command_enforcement(self):
        """Test that BaseCommand cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseCommand(Mock())


class TestCommandValidation:
    """Test command argument validation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = TestableCommand()

    def test_validate_args_no_requirements(self):
        """Test validation with no argument requirements."""
        assert self.command.validate_args([]) is True
        assert self.command.validate_args(["arg1"]) is True
        assert self.command.validate_args(["arg1", "arg2", "arg3"]) is True

    def test_validate_args_minimum_requirements(self):
        """Test validation with minimum argument requirements."""
        # Test with minimum 2 arguments
        assert self.command.validate_args(["arg1", "arg2"], min_args=2) is True
        assert self.command.validate_args(["arg1", "arg2", "arg3"], min_args=2) is True
        assert self.command.validate_args(["arg1"], min_args=2) is False
        assert self.command.validate_args([], min_args=2) is False

    def test_validate_args_maximum_requirements(self):
        """Test validation with maximum argument requirements."""
        # Test with maximum 2 arguments
        assert self.command.validate_args([], max_args=2) is True
        assert self.command.validate_args(["arg1"], max_args=2) is True
        assert self.command.validate_args(["arg1", "arg2"], max_args=2) is True
        assert self.command.validate_args(["arg1", "arg2", "arg3"], max_args=2) is False

    def test_validate_args_min_and_max_requirements(self):
        """Test validation with both min and max requirements."""
        # Require 1-3 arguments
        assert self.command.validate_args([], min_args=1, max_args=3) is False
        assert self.command.validate_args(["arg1"], min_args=1, max_args=3) is True
        assert self.command.validate_args(["arg1", "arg2"], min_args=1, max_args=3) is True
        assert self.command.validate_args(["arg1", "arg2", "arg3"], min_args=1, max_args=3) is True
        assert self.command.validate_args(["a1", "a2", "a3", "a4"], min_args=1, max_args=3) is False

    def test_validate_args_unlimited_max(self):
        """Test validation with unlimited maximum arguments."""
        # min_args=1, max_args=None (unlimited)
        assert self.command.validate_args([], min_args=1, max_args=None) is False
        assert self.command.validate_args(["arg1"], min_args=1, max_args=None) is True
        assert self.command.validate_args(["a1", "a2", "a3", "a4", "a5"], min_args=1, max_args=None) is True

    @patch('builtins.print')
    def test_validate_args_error_messages(self, mock_print):
        """Test that validation errors print appropriate messages."""
        # Test minimum args error
        self.command.validate_args([], min_args=2)
        mock_print.assert_called_with("Error: Command requires at least 2 argument(s)")

        # Test maximum args error  
        mock_print.reset_mock()
        self.command.validate_args(["a1", "a2", "a3"], max_args=2)
        mock_print.assert_called_with("Error: Command accepts at most 2 argument(s)")


class TestCommandOutputMethods:
    """Test command output and messaging functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = TestableCommand()

    @patch('builtins.print')
    def test_print_info(self, mock_print):
        """Test informational message printing."""
        self.command.print_info("Test info message")
        mock_print.assert_called_once_with("Test info message")

    @patch('builtins.print')
    @patch('loguru.logger.warning')
    def test_print_error(self, mock_logger, mock_print):
        """Test error message printing and logging."""
        self.command.print_error("Test error message")
        mock_print.assert_called_once_with("Error: Test error message")
        mock_logger.assert_called_once_with("Command error in testablecommand: Test error message")

    @patch('builtins.print')
    def test_print_success(self, mock_print):
        """Test success message printing."""
        self.command.print_success("Test success message")
        mock_print.assert_called_once_with("Test success message")

    def test_format_list_empty(self):
        """Test formatting empty list."""
        result = self.command.format_list([])
        assert result == "  (none)"

    def test_format_list_with_items(self):
        """Test formatting list with items."""
        items = ["item1", "item2", "item3"]
        result = self.command.format_list(items)
        expected = "  • item1\n  • item2\n  • item3"
        assert result == expected

    def test_format_list_custom_prefix(self):
        """Test formatting list with custom prefix."""
        items = ["item1", "item2"]
        result = self.command.format_list(items, prefix="- ")
        expected = "- item1\n- item2"
        assert result == expected

    def test_get_command_usage_default(self):
        """Test default command usage generation."""
        result = self.command.get_command_usage("/test")
        assert result == "Usage: /test [args...]"


class TestCommandExceptions:
    """Test command exception classes."""

    def test_command_error_basic(self):
        """Test basic CommandError functionality."""
        error = CommandError("Test error message")
        assert str(error) == "Test error message"
        assert error.command is None

    def test_command_error_with_command(self):
        """Test CommandError with command specification."""
        error = CommandError("Test error", command="/test")
        assert str(error) == "Test error"
        assert error.command == "/test"

    def test_command_validation_error(self):
        """Test CommandValidationError inheritance."""
        error = CommandValidationError("Validation failed", command="/validate")
        assert isinstance(error, CommandError)
        assert str(error) == "Validation failed"
        assert error.command == "/validate"

    def test_command_execution_error(self):
        """Test CommandExecutionError inheritance."""
        error = CommandExecutionError("Execution failed", command="/execute")
        assert isinstance(error, CommandError)
        assert str(error) == "Execution failed"
        assert error.command == "/execute"

    def test_exception_hierarchy(self):
        """Test exception inheritance hierarchy."""
        assert issubclass(CommandValidationError, CommandError)
        assert issubclass(CommandExecutionError, CommandError)
        assert issubclass(CommandError, Exception)


class TestCommandIntegration:
    """Integration tests for command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = Mock()
        self.command = TestableCommand(self.mock_registry)

    @pytest.mark.asyncio
    async def test_handle_command_interface(self):
        """Test that handle_command interface works correctly."""
        await self.command.handle_command("/test", ["arg1", "arg2"])
        
        assert self.command.handle_command_called is True
        assert self.command.last_command == "/test"
        assert self.command.last_args == ["arg1", "arg2"]

    def test_registry_integration(self):
        """Test integration with command registry."""
        assert self.command.registry is self.mock_registry

    @patch('builtins.print')
    def test_error_handling_workflow(self, mock_print):
        """Test complete error handling workflow."""
        # Test validation failure
        is_valid = self.command.validate_args([], min_args=1)
        assert is_valid is False
        mock_print.assert_called_with("Error: Command requires at least 1 argument(s)")

        # Test custom error message
        mock_print.reset_mock()
        self.command.print_error("Custom error")
        mock_print.assert_called_with("Error: Custom error")

    def test_command_lifecycle(self):
        """Test complete command lifecycle."""
        # 1. Command creation
        assert isinstance(self.command, BaseCommand)
        assert self.command._command_name == "testablecommand"

        # 2. Validation
        assert self.command.validate_args(["arg1"], min_args=1, max_args=2) is True

        # 3. Usage info
        usage = self.command.get_command_usage("/lifecycle")
        assert "Usage:" in usage
        assert "/lifecycle" in usage