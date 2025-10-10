"""
Information display commands for YACBA CLI.

Handles commands that display information about the current state:
- /history: Display conversation history
- /tools: List currently loaded tools
- /conversation-manager: Show conversation manager info
- /conversation-stats: Show conversation management statistics

Note: /help is handled separately in help_command.py
"""

import json
from typing import List

from repl_toolkit.commands.base import CommandError
from .adapted_commands import AdaptedCommands


class InfoCommands(AdaptedCommands):
    """Handler for information display commands (excluding /help)."""

    def __init__(self, registry, backend):
        super().__init__(registry, backend)

    async def handle_command(self, command: str, args: List[str]) -> None:
        """
        Handle info commands like /history, /tools, /conversation-manager.

        Args:
            command: The command to execute
            args: Command arguments
        """
        try:
            if command == "/history":
                await self._show_history(args)
            elif command == "/tools":
                await self._list_tools(args)
            elif command == "/conversation-manager":
                await self._show_conversation_manager_info(args)
            elif command == "/conversation-stats":
                await self._show_conversation_stats(args)
            else:
                print(f"Unknown info command: {command}")
        except CommandError as e:
            print(f"Command error: {e}")
        except Exception as e:
            print(f"Unexpected error in {command}: {e}")

    async def _show_history(self, args: List[str]) -> None:
        """
        Display the current conversation history as JSON.

        Args:
            args: Should be empty for this command
        """
        if args:
            print("The /history command takes no arguments.")
            return

        try:
            # Access messages through the agent proxy
            agent_proxy = self.backend.get_agent_proxy()
            messages = getattr(agent_proxy, 'messages', [])
            
            if not messages:
                print("No conversation history available.")
                return

            # Format the history nicely
            history_json = json.dumps(messages, indent=2, ensure_ascii=False)
            print("Current conversation history:")
            print(history_json)

        except (TypeError, ValueError) as e:
            print(f"Failed to serialize conversation history: {e}")
        except Exception as e:
            print(f"Failed to display history: {e}")

    async def _list_tools(self, args: List[str]) -> None:
        """
        List all currently loaded tools with their details.

        Args:
            args: Should be empty for this command
        """
        if args:
            print("The /tools command takes no arguments.")
            return

        try:
            tool_names = self.backend.get_tool_names()
            
            if not tool_names:
                print("No tools are currently loaded.")
                return

            print(f"Loaded tools ({len(tool_names)}):")
            for i, tool_name in enumerate(tool_names, 1):
                print(f"  {i}. {tool_name}")

        except Exception as e:
            print(f"Failed to list tools: {e}")

    async def _show_conversation_manager_info(self, args: List[str]) -> None:
        """
        Show information about the current conversation manager configuration.

        Args:
            args: Should be empty for this command
        """
        if args:
            print("The /conversation-manager command takes no arguments.")
            return

        print("Conversation Manager Configuration:")
        print("  Type: strands_agent_factory managed")
        print("  (Detailed configuration info not yet implemented)")

    async def _show_conversation_stats(self, args: List[str]) -> None:
        """
        Show conversation statistics and current memory usage.

        Args:
            args: Should be empty for this command
        """
        if args:
            print("The /conversation-stats command takes no arguments.")
            return

        try:
            stats = await self.backend.get_conversation_stats()
            
            print("Conversation Statistics:")
            print(f"  Current Messages: {stats.get('message_count', 0)}")
            print(f"  Available Tools: {stats.get('tool_count', 0)}")
            
            # Additional stats can be added as backend provides more info

        except Exception as e:
            print(f"Failed to show conversation stats: {e}")

    def get_command_usage(self, command: str) -> str:
        """
        Get usage information for info commands.

        Args:
            command: Command to get usage for

        Returns:
            Usage string
        """
        usage_map = {
            "/history": "/history - Display the current conversation history as JSON",
            "/tools": "/tools - List all currently loaded tools with details",
            "/conversation-manager": "/conversation-manager - Show conversation manager configuration",
            "/conversation-stats": "/conversation-stats - Show conversation statistics and memory usage"
        }

        return usage_map.get(command, super().get_command_usage(command))