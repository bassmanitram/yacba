"""
Session management commands for YACBA CLI.

Handles commands that display information about the current state:
- /session: Display/manage the current persisted session
- /clear: Clear the current conversation

Note: /help is handled separately in help_command.py
"""

from typing import List
import re
from repl_toolkit.commands.base import CommandError
from .adapted_commands import AdaptedCommands


class SessionCommands(AdaptedCommands):
    """Handler for session management commands."""

    def __init__(self, registry, backend):
        super().__init__(registry, backend)

    async def handle_command(self, command: str, args: List[str]) -> None:
        """
        Handle session commands like /session, /clear.

        Args:
            command: The command to execute
            args: Command arguments
        """
        try:
            if command == "/session":
                await self._handle_session(args)
            elif command == "/clear":
                await self._clear_session(args)
            else:
                print(f"Unknown session command: {command}")
        except CommandError as e:
            print(f"Command error: {e}")
        except Exception as e:
            print(f"Unexpected error in {command}: {e}")

    async def _handle_session(self, args: List[str]):
        """Handles the /session command and its subcommands."""
        # For now, implement basic session info - full session management
        # would require additional backend methods
        if not args:
            print("Session management not fully implemented yet.")
            print("Current session: default")
            return

        session_name = args[0]

        # Validate the session name format
        if not re.match(r"^[a-z][a-z0-9_-]*$", session_name):
            print(f"Invalid session name: '{session_name}'.")
            print("Name must be lowercase, start with a letter, and contain "
                  "only letters, numbers, '-', or '_'.")
            return

        print(f"Session switching to '{session_name}' not fully implemented yet.")

    async def _clear_session(self, args: List[str]):
        """Clear the current conversation."""
        success = await self.backend.clear_conversation()
        if success:
            print("Conversation messages cleared")
        else:
            print("Failed to clear conversation")