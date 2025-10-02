"""
Session management commands for YACBA CLI.

Handles commands that display information about the current state:
- /session: Display/manage the current persisted session
- /clear: Clear the current conversation

Note: /help is handled separately in help_command.py
"""

from typing import List
import re
from cli.commands.base_command import CommandError
from .adapted_commands import AdaptedCommands


class SessionCommands(AdaptedCommands):
    """Handler for information display commands (excluding /help)."""

    def __init__(self, registry, engine):
        super().__init__(registry, engine)

    async def handle_command(self, command: str, args: List[str]) -> None:
        """
        Handle info commands like /session, /clear.

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
                self.print_error(f"Unknown info command: {command}")
        except CommandError as e:
            self.print_error(str(e))
        except Exception as e:
            self.print_error(f"Unexpected error in {command}: {e}")

    async def _handle_session(self, args: List[str]):
        """Handles the /session command and its subcommands."""
        session_manager = self.engine.session_manager

        #  : Case 1: /session (no arguments)
        if not args:
            sessions = session_manager.list_sessions()
            if sessions:
                print("Available sessions:")
                for s_name in sessions:
                    marker = ("*" if s_name == session_manager.session_id
                              else " ")
                    print(f"  {marker} {s_name}")
            else:
                print("No saved sessions found.")
            return

        session_name = args[0]

        # : Case 2: Validate the session name format
        if not re.match(r"^[a-z][a-z0-9_-]*$", session_name):
            print(f"Invalid session name: '{session_name}'.")
            print("Name must be lowercase, start with a letter, and contain "
                  "only letters, numbers, '-', or '_'.")
            return

        #  : Case 5: Already in the requested session
        if session_manager.session_id == session_name:
            print(f"Already in session '{session_name}'.")
            return

        #  : Case 6: Switch to the new session
        session_manager.set_active_session(session_name)
        print(f"Switched to session '{session_name}'.")

    async def _clear_session(self, args: List[str]):
        self.engine.session_manager.clear()
        print("Conversation messages cleared")
