"""
Information display commands for YACBA CLI.

Handles commands that display information about the current state:
- /history: Display conversation history
- /tools: List currently loaded tools

Note: /help is handled separately in help_command.py
"""

import json
from typing import List

from cli.commands.base_command import CommandError
from adapted_commands import AdaptedCommands


class InfoCommands(AdaptedCommands):
    """Handler for information display commands (excluding /help)."""

    def __init__(self, engine):
        super().__init__(engine)
    
    async def handle_command(self, command: str, args: List[str]) -> None:
        """
        Handle info commands like /history, /tools.
        
        Args:
            command: The command to execute
            args: Command arguments
        """
        try:
            if command == "/history":
                await self._show_history(args)
            elif command == "/tools":
                await self._list_tools(args)
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
        
        if not self.check_engine_ready():
            return
        
        try:
            if not self.agent.messages:
                self.print_info("No conversation history available.")
                return
            
            # Format the history nicely
            history_json = json.dumps(self.agent.messages, indent=2, ensure_ascii=False)
            self.print_info("Current conversation history:")
            self.print_info(history_json)
            
        except json.JSONEncodeError as e:
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
        
        if not self.engine.is_ready():
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
    
    def _get_tool_info(self, tool, index: int) -> str:
        """
        Extract information about a tool for display.
        
        Args:
            tool: The tool object to analyze
            index: Tool index number
            
        Returns:
            Formatted tool information string
        """
        # Try multiple ways to get a meaningful tool name
        tool_name = "unnamed-tool"
        tool_description = None
        tool_source = "unknown"
        
        # Method 1: Check for tool_spec (most reliable for MCP tools)
        if hasattr(tool, 'tool_spec') and isinstance(tool.tool_spec, dict):
            spec = tool.tool_spec
            tool_name = spec.get('name', tool_name)
            tool_description = spec.get('description')
            
            # Try to determine source from tool spec
            if 'mcp' in str(type(tool)).lower():
                tool_source = "MCP"
            elif hasattr(tool, '__module__'):
                tool_source = f"Python ({tool.__module__})"
        
        # Method 2: Check function attributes
        elif hasattr(tool, '__name__'):
            tool_name = tool.__name__
            if hasattr(tool, '__module__'):
                tool_source = f"Python ({tool.__module__})"
        
        # Method 3: Use class name as fallback
        elif hasattr(tool, '__class__'):
            tool_name = tool.__class__.__name__
            tool_source = f"Class ({tool.__class__.__module__})"
        
        # Format the output
        info_parts = [f"  {index}. {tool_name}"]
        
        if tool_description:
            # Truncate long descriptions
            if len(tool_description) > 80:
                tool_description = tool_description[:77] + "..."
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
            "/history": "/history - Display the current conversation history as JSON",
            "/tools": "/tools - List all currently loaded tools with details"
        }
        
        return usage_map.get(command, super().get_command_usage(command))
