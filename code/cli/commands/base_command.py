"""
Base command class for YACBA CLI meta-commands.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from loguru import logger

from yacba_types.cli import CliCommandRegistry


class BaseCommand(ABC):
    """
    Abstract base class for CLI meta-commands.

    Provides common functionality and enforces a consistent interface
    for all command handlers.
    """

    def __init__(self, registry: CliCommandRegistry):
        """
        Initialize the command handler.

        Args:
            manager: The ChatbotManager instance for accessing engine state
        """
        self._command_name = self.__class__.__name__.lower().replace('commands', '')
        self.registry = registry

    @abstractmethod
    async def handle_command(self, command: str, args: List[str]) -> None:
        """
        Handle a specific command with arguments.

        Args:
            command: The command string (e.g., '/help')
            args: List of command arguments

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass

    def validate_args(self, args: List[str], min_args: int = 0, max_args: Optional[int] = None) -> bool:
        """
        Validate command arguments.

        Args:
            args: Arguments to validate
            min_args: Minimum number of arguments required
            max_args: Maximum number of arguments allowed (None for unlimited)

        Returns:
            True if arguments are valid, False otherwise
        """
        if len(args) < min_args:
            self.print_error(f"Command requires at least {min_args} argument(s)")
            return False

        if max_args is not None and len(args) > max_args:
            self.print_error(f"Command accepts at most {max_args} argument(s)")
            return False

        return True

    def print_info(self, message: str) -> None:
        """Print an informational message."""
        print(message)

    def print_error(self, message: str) -> None:
        """Print an error message."""
        print(f"Error: {message}")
        logger.warning(f"Command error in {self._command_name}: {message}")

    def print_success(self, message: str) -> None:
        """Print a success message."""
        print(message)

    def format_list(self, items: List[str], prefix: str = "  • ") -> str:
        """
        Format a list of items for display.

        Args:
            items: Items to format
            prefix: Prefix for each item

        Returns:
            Formatted string
        """
        if not items:
            return "  (none)"

        return "\n".join(f"{prefix}{item}" for item in items)

    def get_command_usage(self, command: str) -> str:
        """
        Get usage information for a command.

        Args:
            command: Command to get usage for

        Returns:
            Usage string
        """
        # This would typically be overridden by subclasses
        # or pull from the command registry
        return f"Usage: {command} [args...]"


class CommandError(Exception):
    """Exception raised when a command encounters an error."""

    def __init__(self, message: str, command: str = None):
        """
        Initialize command error.

        Args:
            message: Error message
            command: Command that caused the error (optional)
        """
        super().__init__(message)
        self.command = command


class CommandValidationError(CommandError):
    """Exception raised when command arguments are invalid."""
    pass


class CommandExecutionError(CommandError):
    """Exception raised when command execution fails."""
    pass
