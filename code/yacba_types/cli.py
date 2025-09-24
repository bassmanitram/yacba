"""
Type definitions for the CLI.
"""
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CliCommandRegistry(Protocol):
	"""
	Protocol for CLI command registry that YACBA manages.
	These handle command registration, execution, help retrieval.
	"""
	
	def get_command_help(self, command: str) -> str:
		"""Retrieve help text for a specific command."""
		...

	def validate_command(self, command: str) -> bool:
		"""Validate if a command is supported."""
		...

	def get_all_commands(self) -> dict[str, dict]:
		"""Get all registered commands."""
		...

	def get_command_handler(self, command: str) -> Any:
		"""Get the handler instance for a specific command."""
		...
	
	def handle_command(self, command: str, args: list[str]) -> None:
		"""Handle a command by invoking its handler."""
		...
