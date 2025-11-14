"""
Information display actions for YACBA CLI.

Handles actions that display information about the current state:
- /history: Display conversation history
- /tools: List currently loaded tools
- /conversation-manager: Show conversation manager info
- /conversation-stats: Show conversation management statistics
"""

import json
from typing import TYPE_CHECKING

from utils.general_utils import custom_json_serializer_for_display
from repl_toolkit import Action, ActionContext, ActionRegistry

def handle_history(context: ActionContext) -> None:
    """Display the current conversation history as JSON."""
    backend = context.backend
    args = context.args
    
    try:
        if args:
            print("The /history command takes no arguments.")
            return

        # Access messages through the agent proxy
        agent_proxy = backend.get_agent_proxy()
        messages = getattr(agent_proxy, 'messages', [])
        
        if not messages:
            print("No conversation history available.")
            return

        # Format the history nicely
        history_json = json.dumps(messages, indent=2, ensure_ascii=False, default=custom_json_serializer_for_display)
        print("Current conversation history:")
        print(history_json)

    except (TypeError, ValueError) as e:
        print(f"Failed to serialize conversation history: {e}")
    except Exception as e:
        print(f"Failed to display history: {e}")


def handle_tools(context: ActionContext) -> None:
    """List all currently loaded tools with their details."""
    backend = context.backend
    args = context.args
    
    try:
        if args:
            print("The /tools command takes no arguments.")
            return

        tool_names = backend.get_tool_names()
        
        if not tool_names:
            print("No tools are currently loaded.")
            return

        print(f"Loaded tools ({len(tool_names)}):")
        for i, tool_name in enumerate(tool_names, 1):
            print(f"  {i}. {tool_name}")

    except Exception as e:
        print(f"Failed to list tools: {e}")


def handle_conversation_manager(context: ActionContext) -> None:
    """Show information about the current conversation manager configuration."""
    args = context.args
    
    try:
        if args:
            print("The /conversation-manager command takes no arguments.")
            return

        print("Conversation Manager Configuration:")
        print("  Type: strands_agent_factory managed")
        print("  (Detailed configuration info not yet implemented)")
        
    except Exception as e:
        print(f"Failed to show conversation manager info: {e}")


def handle_conversation_stats(context: ActionContext) -> None:
    """Show conversation statistics and current memory usage."""
    backend = context.backend
    args = context.args
    
    try:
        if args:
            print("The /conversation-stats command takes no arguments.")
            return

        stats = backend.get_conversation_stats()
        
        print("Conversation Statistics:")
        print(f"  Current Messages: {stats.get('message_count', 0)}")
        print(f"  Available Tools: {stats.get('tool_count', 0)}")
        
        # Additional stats can be added as backend provides more info

    except Exception as e:
        print(f"Failed to show conversation stats: {e}")


def register_info_actions(registry: ActionRegistry) -> None:
    """Register information display actions."""
    
    history_action = Action(
        name="history",
        command="/history",
        handler=handle_history,
        category="Information",
        description="Show conversation history",
        command_usage="/history - Display message history as JSON"
    )
    
    tools_action = Action(
        name="tools",
        command="/tools",
        handler=handle_tools,
        category="Information", 
        description="List available tools",
        command_usage="/tools - Show currently loaded tools"
    )
    
    conversation_manager_action = Action(
        name="conversation-manager",
        command="/conversation-manager",
        handler=handle_conversation_manager,
        category="Information",
        description="Show conversation manager configuration",
        command_usage="/conversation-manager - Display current conversation management settings"
    )
    
    conversation_stats_action = Action(
        name="conversation-stats", 
        command="/conversation-stats",
        handler=handle_conversation_stats,
        category="Information",
        description="Show conversation statistics",
        command_usage="/conversation-stats - Display conversation memory usage and statistics"
    )
    
    registry.register_action(history_action)
    registry.register_action(tools_action)
    registry.register_action(conversation_manager_action)
    registry.register_action(conversation_stats_action)