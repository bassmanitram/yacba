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

from .adapted_commands import AdaptedCommands
from repl_toolkit.commands import CommandError

class InfoCommands(AdaptedCommands):
    """Handler for information display commands (excluding /help)."""

    def __init__(self, registry, engine):
        super().__init__(registry, engine)

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
                self.print_error(f"Unknown info command: {command}")
        except CommandError as e:
            self.print_error(str(e))
        except Exception as e:
            self.print_error(f"Unexpected error in {command}: {e}")

    async def _show_history(self, args: List[str]) -> None:
        """
        Display the current conversation history as JSON.

        Args:
            args: Should be empty for this command
        """
        if not self.validate_args(args, max_args=0):
            return

        if not self.engine.is_ready:
            return

        try:
            if not self.agent.messages:
                self.print_info("No conversation history available.")
                return

            #  Format the history nicely
            history_json = json.dumps(self.agent.messages, indent=2,
                                      ensure_ascii=False)
            self.print_info(": Current conversation history:")
            self.print_info(history_json)

        except (TypeError, ValueError) as e:
            self.print_error(f"Failed to serialize conversation history: {e}")
        except Exception as e:
            self.print_error(f"Failed to display history: {e}")

    async def _list_tools(self, args: List[str]) -> None:
        """
        List all currently loaded tools with their details.

        Args:
            args: Should be empty for this command
        """
        if not self.validate_args(args, max_args=0):
            return

        if not self.engine.is_ready:
            return

        try:
            loaded_tools = self.engine.loaded_tools

            if not loaded_tools:
                self.print_info("No tools are currently loaded.")
                return

            self.print_info(f"Loaded tools ({len(loaded_tools)}):")

            for i, tool in enumerate(loaded_tools, 1):
                tool_info = self._get_tool_info(tool, i)
                self.print_info(tool_info)

        except Exception as e:
            self.print_error(f"Failed to list tools: {e}")

    async def _show_conversation_manager_info(self,
                                              args: List[str]) -> None:
        """
        Show information about the current conversation manager configuration.

        Args:
            args: Should be empty for this command
        """
        if not self.validate_args(args, max_args=0):
            return

        if not self.engine.is_ready:
            return

        try:
            config = self.engine.config
            manager = self.engine.conversation_manager

            self.print_info("Conversation Manager Configuration:")
            self.print_info(f"  Type: {config.conversation_manager_type}")

            if config.conversation_manager_type == "sliding_window":
                self.print_info("  Window Size: "
                                f"{config.sliding_window_size} messages")
                truncate_text = ('Yes' if config.should_truncate_results
                                 else 'No')
                self.print_info(f"  Truncate Results: {truncate_text}")

            elif config.conversation_manager_type == "summarizing":
                ratio_percent = int(config.summary_ratio * 100)
                self.print_info(f"  Summary Ratio: {config.summary_ratio} "
                                f"({ratio_percent}%)")
                self.print_info("  Preserve Recent: "
                                f"{config.preserve_recent_messages} messages")
                if config.summarization_model:
                    self.print_info("  Summarization Model: "
                                    f"{config.summarization_model}")
                else:
                    self.print_info("  Summarization Model: Same as main "
                                    f"model ({config.model_string})")
                if config.custom_summarization_prompt:
                    self.print_info("  Custom Prompt: Yes")
                else:
                    self.print_info("  Custom Prompt: No (using default)")

            elif config.conversation_manager_type == "null":
                self.print_info("  No conversation management "
                                "(all history preserved)")

            #  : Show current state if manager exists
            if (manager and hasattr(manager, 'removed_message_count')):
                self.print_info("  Messages Removed: "
                                f"{manager.removed_message_count}")

        except Exception as e:
            self.print_error(f"Failed to show conversation manager info: {e}")

    async def _show_conversation_stats(self, args: List[str]) -> None:
        """
        Show conversation statistics and current memory usage.

        Args:
            args: Should be empty for this command
        """
        if not self.validate_args(args, max_args=0):
            return

        if not self.engine.is_ready:
            return

        try:
            agent = self.agent
            manager = self.engine.conversation_manager

            current_messages = len(agent.messages) if agent.messages else 0
            total_removed = (manager.removed_message_count
                             if (manager and
                                 hasattr(manager, 'removed_message_count'))
                             else 0)
            total_processed = current_messages + total_removed

            self.print_info("Conversation Statistics:")
            self.print_info(f"  Current Messages: {current_messages}")
            self.print_info(f"  Removed Messages: {total_removed}")
            self.print_info(f"  Total Processed: {total_processed}")

            if total_processed > 0:
                retention_rate = (current_messages / total_processed) * 100
                self.print_info(f"  Retention Rate: {retention_rate:.1f}%")

            #  : Show message breakdown if we have messages
            if agent.messages:
                user_messages = sum(1 for msg in agent.messages
                                    if msg.get('role') == 'user')
                assistant_messages = sum(1 for msg in agent.messages
                                         if msg.get('role') == 'assistant')
                other_messages = (current_messages - user_messages -
                                  assistant_messages)

                self.print_info("  Message Breakdown:")
                self.print_info(f"    User: {user_messages}")
                self.print_info(f"    Assistant: {assistant_messages}")
                if other_messages > 0:
                    self.print_info(f"    Other: {other_messages}")

                #  Check for tool use messages
                tool_use_messages = sum(
                    1 for msg in agent.messages
                    if any('toolUse' in str(content)
                           for content in msg.get('content', []))
                )
                tool_result_messages = sum(
                    1 for msg in agent.messages
                    if any('tool: Result' in str(content)
                           for content in msg.get('content', []))
                )

                if tool_use_messages > 0 or tool_result_messages > 0:
                    self.print_info("  Tool Messages:")
                    self.print_info(f"    Tool Use: {tool_use_messages}")
                    self.print_info(f"    Tool Results: {tool_result_messages}")

        except Exception as e:
            self.print_error(f"Failed to show conversation stats: {e}")

    def _get_tool_info(self, tool, index: int) -> str:
        """
        Extract information about a tool for display.

        Args:
            tool: The tool object to analyze
            index: Tool index number

        Returns:
            Formatted tool information string
        """
        #  Try multiple ways to get a meaningful tool name
        tool_name = "unnamed-tool"
        tool_description = None
        tool_source = "unknown"

        # : Method 1: Check for tool_spec (most reliable for MCP tools)
        if hasattr(tool, 'tool_spec') and isinstance(tool.tool_spec, dict):
            spec = tool.tool_spec
            tool_name = spec.get('name', tool_name)
            tool_description = spec.get('description')

            #  : Try to determine source from tool spec
            if 'mcp' in str(type(tool)).lower():
                tool_source = "MCP"
            elif hasattr(tool, '__module__'):
                tool_source = f"Python ({tool.__module__})"

        #  : Method 2: Check function attributes
        elif hasattr(tool, '__name__'):
            tool_name = tool.__name__
            if hasattr(tool, '__module__'):
                tool_source = f"Python ({tool.__module__})"

        #  : Method 3: Use class name as fallback
        elif hasattr(tool, '__class__'):
            tool_name = tool.__class__.__name__
            tool_source = f"Class ({tool.__class__.__module__})"

        #  : Format the output
        info_parts = [f"  {index}. {tool_name}"]

        if tool_description:
            #  : Truncate long descriptions
            if len(tool_description) > 80:
                tool_description = tool_description[: 77] + "..."
            info_parts.append(f" - {tool_description}")

        info_parts.append(f" [{tool_source}]")

        return "".join(info_parts)

    def get_command_usage(self, command: str) -> str:
        """
        Get usage information for info commands.

        Args:
            command: Command to get usage for

        Returns:
            Usage string
        """
        usage_map = {
            "/history": "/history - Display the current conversation "
                        "history as JSON",
            "/tools": "/tools - List all currently loaded tools with details",
            "/conversation-manager": "/conversation-manager - Show "
                                     "conversation manager configuration",
            "/conversation-stats": "/conversation-stats - Show conversation "
                                   "statistics and memory usage"
        }

        return usage_map.get(command, super().get_command_usage(command))