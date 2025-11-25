"""
Information display actions for YACBA CLI.

Handles actions that display information about the current state:
- /history: Display conversation history
- /tools: List currently loaded tools
- /conversation-manager: Show conversation manager info
- /conversation-stats: Show conversation management statistics
"""

import json
import re
from collections import defaultdict
from typing import Dict, List

from utils.general_utils import custom_json_serializer_for_display
from repl_toolkit import Action, ActionContext, ActionRegistry


def handle_history(context: ActionContext) -> None:
    """Display the current conversation history as JSON."""
    backend = context.backend
    args = context.args
    printer = context.printer

    try:
        if args:
            printer("The /history command takes no arguments.")
            return

        # Access messages through the agent proxy
        agent_proxy = backend.get_agent_proxy()
        messages = getattr(agent_proxy, "messages", [])

        if not messages:
            printer("No conversation history available.")
            return

        # Format the history nicely
        history_json = json.dumps(
            messages,
            indent=2,
            ensure_ascii=False,
            default=custom_json_serializer_for_display,
        )
        printer("Current conversation history:")
        printer(history_json)

    except (TypeError, ValueError) as e:
        printer(f"Failed to serialize conversation history: {e}")
    except Exception as e:
        printer(f"Failed to display history: {e}")


def handle_tools(context: ActionContext) -> None:
    """List all currently loaded tools in a friendly, organized format."""
    backend = context.backend
    args = context.args
    printer = context.printer

    try:
        if args:
            printer("The /tools command takes no arguments.")
            return

        # Get tool details from backend
        tool_details = backend.get_tool_details()

        if not tool_details:
            printer("No tools are currently loaded.")
            return

        # Group tools by category
        grouped_tools = _group_tools_by_category(tool_details)

        # Count total tools
        total_tools = sum(len(tools) for tools in grouped_tools.values())

        printer(f"\nCurrently loaded tools ({total_tools}):")
        printer("")

        # Display each category
        for category, tools in sorted(grouped_tools.items()):
            printer(f"{category}:")

            # Find max tool name length for alignment
            max_name_len = max(len(tool["name"]) for tool in tools)

            for tool in sorted(tools, key=lambda t: t["name"]):
                name = tool["name"]
                description = tool.get("description", "No description available")

                # Truncate long descriptions
                description = _truncate_description(description, max_length=80)

                # Align descriptions
                printer(f"  {name:<{max_name_len}}  - {description}")

            printer("")

    except Exception as e:
        printer(f"Failed to list tools: {e}")


def _truncate_description(description: str, max_length: int = 80) -> str:
    """
    Truncate description intelligently:
    - If length < max, use full string
    - Else extract first sentence, truncate with ellipsis if still too long

    Args:
        description: The description text
        max_length: Maximum length before truncation

    Returns:
        Truncated description string
    """
    if not description or description == "No description available":
        return description

    # Remove extra whitespace
    description = " ".join(description.split())

    # If already short enough, return as-is
    if len(description) <= max_length:
        return description

    # Extract first sentence
    # Match sentence ending with . ! ? followed by space or end of string
    sentence_match = re.match(r"^(.*?[.!?])(?:\s|$)", description)

    if sentence_match:
        first_sentence = sentence_match.group(1)
        # If first sentence fits, use it
        if len(first_sentence) <= max_length:
            return first_sentence
        # Otherwise truncate the first sentence with ellipsis
        return first_sentence[: max_length - 3] + "..."

    # No sentence boundary found, just truncate
    return description[: max_length - 3] + "..."


def _group_tools_by_category(tool_details: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group tools by category based on their source.

    Args:
        tool_details: List of tool detail dictionaries

    Returns:
        Dictionary mapping category names to lists of tools
    """
    grouped = defaultdict(list)

    for tool in tool_details:
        source_type = tool.get("source_type", "unknown")
        source_id = tool.get("source_id", "")

        # Determine category
        if source_type == "python":
            category = _categorize_python_tool(tool["name"], source_id)
        elif source_type == "mcp":
            category = f"MCP Tools ({source_id})"
        elif source_type == "a2a":
            category = f"A2A Agents ({source_id})"
        else:
            category = "Other Tools"

        grouped[category].append(tool)

    return dict(grouped)


def _categorize_python_tool(tool_name: str, source_id: str) -> str:
    """
    Categorize Python tools based on name patterns.

    Args:
        tool_name: Name of the tool
        source_id: Source identifier

    Returns:
        Category string
    """
    name_lower = tool_name.lower()

    # File system operations
    if any(
        word in name_lower
        for word in ["file", "read", "write", "directory", "path", "list_dir"]
    ):
        return "File System Tools"

    # Code execution
    if any(
        word in name_lower
        for word in ["execute", "run", "eval", "shell", "bash", "python"]
    ):
        return "Code Execution"

    # Web/Network
    if any(
        word in name_lower
        for word in ["http", "url", "fetch", "download", "web", "api", "request"]
    ):
        return "Web Access"

    # Search
    if any(word in name_lower for word in ["search", "find", "query", "lookup"]):
        return "Search Tools"

    # Database
    if any(word in name_lower for word in ["database", "db", "sql", "query"]):
        return "Database Tools"

    # Default: use source_id or generic
    if source_id and source_id != "unknown":
        return f"Python Tools ({source_id})"

    return "Python Tools"


def handle_conversation_manager(context: ActionContext) -> None:
    """Show information about the current conversation manager configuration."""
    args = context.args
    printer = context.printer

    try:
        if args:
            printer("The /conversation-manager command takes no arguments.")
            return

        printer("Conversation Manager Configuration:")
        printer("  Type: strands_agent_factory managed")
        printer("  (Detailed configuration info not yet implemented)")

    except Exception as e:
        printer(f"Failed to show conversation manager info: {e}")


def handle_conversation_stats(context: ActionContext) -> None:
    """Show conversation statistics and current memory usage."""
    backend = context.backend
    args = context.args
    printer = context.printer

    try:
        if args:
            printer("The /conversation-stats command takes no arguments.")
            return

        stats = backend.get_conversation_stats()

        printer("Conversation Statistics:")
        printer(f"  Current Messages: {stats.get('message_count', 0)}")
        printer(f"  Available Tools: {stats.get('tool_count', 0)}")

        # Additional stats can be added as backend provides more info

    except Exception as e:
        printer(f"Failed to show conversation stats: {e}")


def register_info_actions(registry: ActionRegistry) -> None:
    """Register information display actions."""

    history_action = Action(
        name="history",
        command="/history",
        handler=handle_history,
        category="Information",
        description="Show conversation history",
        command_usage="/history - Display message history as JSON",
    )

    tools_action = Action(
        name="tools",
        command="/tools",
        handler=handle_tools,
        category="Information",
        description="List available tools",
        command_usage="/tools - Show currently loaded tools",
    )

    conversation_manager_action = Action(
        name="conversation-manager",
        command="/conversation-manager",
        handler=handle_conversation_manager,
        category="Information",
        description="Show conversation manager configuration",
        command_usage="/conversation-manager - Display current conversation management settings",
    )

    conversation_stats_action = Action(
        name="conversation-stats",
        command="/conversation-stats",
        handler=handle_conversation_stats,
        category="Information",
        description="Show conversation statistics",
        command_usage="/conversation-stats - Display conversation memory usage and statistics",
    )

    registry.register_action(history_action)
    registry.register_action(tools_action)
    registry.register_action(conversation_manager_action)
    registry.register_action(conversation_stats_action)
