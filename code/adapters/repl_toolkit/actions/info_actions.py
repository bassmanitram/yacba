"""
Information display actions for YACBA CLI.

Handles actions that display information about the current state:
- /history: Display conversation history
- /tools: List currently loaded tools
- /conv: Show conversation manager configuration and statistics
"""

import json
import re
from collections import defaultdict
from typing import Dict, List

from utils.general_utils import custom_json_serializer_for_display
from repl_toolkit import Action, ActionContext, ActionRegistry


def handle_history(context: ActionContext) -> None:
    """Display the current conversation history."""
    backend = context.backend
    args = context.args
    printer = context.printer

    try:
        # Check for --json flag
        show_json = "--json" in args
        
        if args and not show_json:
            printer("Usage: /history [--json]")
            printer("  --json: Show full JSON representation")
            return

        # Access messages through the agent proxy
        agent_proxy = backend.get_agent_proxy()
        messages = getattr(agent_proxy, "messages", [])

        if not messages:
            printer("No conversation history available.")
            return

        if show_json:
            # Original JSON format
            history_json = json.dumps(
                messages,
                indent=2,
                ensure_ascii=False,
                default=custom_json_serializer_for_display,
            )
            printer("Current conversation history:")
            printer(history_json)
        else:
            # Human-readable format with positions
            _display_history_readable(messages, printer)

    except (TypeError, ValueError) as e:
        printer(f"Failed to serialize conversation history: {e}")
    except Exception as e:
        printer(f"Failed to display history: {e}")


def _display_history_readable(messages: List, printer) -> None:
    """
    Display conversation history in human-readable format with positions.
    
    Format:
        [0] user: "First message..."
        [1] assistant: "Response..." [tool_use: shell]
        [2] tool_result: "Success: output..." (150 chars)
      * [3] user: "Next question..."
    """
    printer(f"Current conversation history ({len(messages)} messages):")
    printer("")
    
    # Calculate width needed for position numbers
    max_pos = len(messages) - 1
    pos_width = len(str(max_pos))
    
    for idx, msg in enumerate(messages):
        # Handle both dict and Pydantic model objects
        if hasattr(msg, 'model_dump'):
            msg_dict = msg.model_dump()
        elif isinstance(msg, dict):
            msg_dict = msg
        else:
            msg_dict = {"role": str(type(msg)), "content": str(msg)}
        
        role = msg_dict.get("role", "unknown")
        
        # Check if this is actually a tool result message (role=user but contains toolResult)
        is_tool_result_msg, tool_result_summary = _check_tool_result_message(msg_dict)
        
        # Format position with proper width and marker
        if role == "user" and not is_tool_result_msg:
            marker = "*"
        else:
            marker = " "
        
        pos_str = f"{marker} [{idx:>{pos_width}}]"
        
        if is_tool_result_msg:
            # Display as tool result, not user message
            printer(f"{pos_str} tool_result: {tool_result_summary}")
            
        elif role == "user":
            text_preview, tool_info = _extract_message_summary(msg_dict)
            if text_preview:
                line = f"{pos_str} user: {text_preview}"
                if tool_info:
                    line += f" {tool_info}"
                printer(line)
            elif tool_info:
                printer(f"{pos_str} user: {tool_info}")
            else:
                printer(f"{pos_str} user: (empty)")
            
        elif role == "assistant":
            text_preview, tool_info = _extract_message_summary(msg_dict)
            if text_preview:
                line = f"{pos_str} assistant: {text_preview}"
                if tool_info:
                    line += f" {tool_info}"
                printer(line)
            elif tool_info:
                printer(f"{pos_str} assistant: {tool_info}")
            else:
                printer(f"{pos_str} assistant: (empty)")
            
        elif role == "tool":
            # Standard tool role (not strands format)
            tool_name = msg_dict.get("tool_name", "unknown")
            content = msg_dict.get("content", "")
            if hasattr(content, '__str__'):
                content_str = str(content)
            else:
                content_str = content
            line_count = content_str.count('\n') + 1 if content_str else 0
            printer(f"{pos_str} tool_result: {tool_name} ({line_count} lines)")
            
        else:
            # Other roles (system, etc.)
            text_preview, tool_info = _extract_message_summary(msg_dict)
            if text_preview:
                printer(f"{pos_str} {role}: {text_preview}")
            elif tool_info:
                printer(f"{pos_str} {role}: {tool_info}")
            else:
                printer(f"{pos_str} {role}: (empty)")
    
    printer("")
    printer("Use /history --json for full JSON representation")


def _check_tool_result_message(msg_dict: Dict) -> tuple[bool, str]:
    """
    Check if a message is actually a tool result (strands format with toolResult in content).
    
    Returns:
        (is_tool_result, summary) where:
        - is_tool_result: True if this message contains toolResult
        - summary: Formatted summary of the tool result
    """
    content = msg_dict.get("content", "")
    
    # Handle Pydantic model objects
    if hasattr(content, 'model_dump'):
        content = content.model_dump()
    
    # Check if content is a list with toolResult
    if isinstance(content, list):
        for part in content:
            # Handle Pydantic models
            if hasattr(part, 'model_dump'):
                part = part.model_dump()
            
            if isinstance(part, dict) and "toolResult" in part:
                tool_result = part["toolResult"]
                status = tool_result.get("status", "unknown")
                result_content = tool_result.get("content", [])
                
                # Extract text from result content
                text_parts = []
                if isinstance(result_content, list):
                    for result_part in result_content:
                        if hasattr(result_part, 'model_dump'):
                            result_part = result_part.model_dump()
                        if isinstance(result_part, dict) and "text" in result_part:
                            text_parts.append(result_part["text"])
                        elif isinstance(result_part, str):
                            text_parts.append(result_part)
                elif isinstance(result_content, str):
                    text_parts.append(result_content)
                
                combined_text = " ".join(text_parts)
                # Remove extra whitespace
                combined_text = " ".join(combined_text.split())
                
                # Create summary
                char_count = len(combined_text)
                preview = combined_text[:100] + "..." if len(combined_text) > 100 else combined_text
                summary = f'"{preview}" ({status}, {char_count} chars)'
                
                return True, summary
    
    return False, ""


def _extract_message_summary(msg_dict: Dict) -> tuple[str, str]:
    """
    Extract text preview and tool information from a message.
    
    Returns:
        (text_preview, tool_info) where:
        - text_preview: Truncated text content or empty string
        - tool_info: Tool usage summary like "[tool_use: shell]" or empty string
    """
    content = msg_dict.get("content", "")
    
    # Handle Pydantic model objects
    if hasattr(content, 'model_dump'):
        content = content.model_dump()
    
    # Simple string content
    if isinstance(content, str):
        return _truncate_message(content, max_length=80), ""
    
    # Array of content parts (e.g., text + tool_use + images)
    if isinstance(content, list):
        text_parts = []
        tool_uses = []
        has_image = False
        
        for part in content:
            # Handle Pydantic models in list
            if hasattr(part, 'model_dump'):
                part = part.model_dump()
                
            if isinstance(part, dict):
                # Check for toolUse (strands format)
                if "toolUse" in part:
                    tool_use = part["toolUse"]
                    tool_name = tool_use.get("name", "unknown")
                    tool_uses.append(tool_name)
                    continue
                
                # Skip toolResult here (handled separately)
                if "toolResult" in part:
                    continue
                
                # TextPart (with 'text' key)
                if "text" in part and isinstance(part["text"], str):
                    text = part["text"]
                    if text:
                        text_parts.append(text)
                    continue
                
                # Standard type-based parts
                part_type = part.get("type", "")
                
                if part_type == "text":
                    text = part.get("text", "")
                    if text:
                        text_parts.append(text)
                elif part_type == "image":
                    has_image = True
                elif part_type == "tool_use":
                    tool_name = part.get("name", part.get("tool_name", "unknown"))
                    tool_uses.append(tool_name)
                    
            elif isinstance(part, str):
                text_parts.append(part)
        
        # Build text preview
        text_preview = ""
        if text_parts:
            combined_text = " ".join(text_parts)
            text_preview = _truncate_message(combined_text, max_length=80)
        
        # Build tool info
        tool_info_parts = []
        if tool_uses:
            if len(tool_uses) == 1:
                tool_info_parts.append(f"[tool_use: {tool_uses[0]}]")
            else:
                tool_info_parts.append(f"[tool_use: {', '.join(tool_uses)}]")
        if has_image:
            tool_info_parts.append("[image]")
        
        tool_info = " ".join(tool_info_parts)
        
        return text_preview, tool_info
    
    # Dict with text field
    if isinstance(content, dict) and "text" in content:
        return _truncate_message(content["text"], max_length=80), ""
    
    # Fallback: convert to string
    content_str = str(content)
    if content_str and content_str != "None":
        return _truncate_message(content_str, max_length=80), ""
    
    return "", ""


def _truncate_message(content: str, max_length: int = 80) -> str:
    """
    Truncate message content for display.
    
    Args:
        content: Message content
        max_length: Maximum length before truncation
        
    Returns:
        Truncated string with ellipsis if needed (includes quotes)
    """
    if not content or content == "":
        return ""
    
    # Remove extra whitespace and newlines
    content = " ".join(content.split())
    
    if len(content) <= max_length:
        return f'"{content}"'
    
    return f'"{content[:max_length-3]}..."'


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


def handle_conv(context: ActionContext) -> None:
    """Show conversation manager configuration and statistics."""
    backend = context.backend
    args = context.args
    printer = context.printer

    try:
        if args:
            printer("The /conv command takes no arguments.")
            return

        config = backend.config
        
        # Get message counts by role
        messages = backend.get_agent_proxy().messages or []
        user_msgs = sum(1 for m in messages if m.get('role') == 'user')
        assistant_msgs = sum(1 for m in messages if m.get('role') == 'assistant')
        total_msgs = len(messages)
        
        printer("Conversation Manager:")
        printer(f"  Messages: {total_msgs} (user: {user_msgs}, assistant: {assistant_msgs})")
        
        # Show configuration if available
        if config:
            if hasattr(config, 'conversation_manager_type'):
                printer(f"  Type: {config.conversation_manager_type}")
            if hasattr(config, 'sliding_window_size'):
                printer(f"  Window: {config.sliding_window_size}")
            if hasattr(config, 'preserve_recent_messages'):
                printer(f"  Preserve Recent: {config.preserve_recent_messages}")

    except Exception as e:
        printer(f"Failed to show conversation info: {e}")


def register_info_actions(registry: ActionRegistry) -> None:
    """Register information display actions."""

    history_action = Action(
        name="history",
        command="/history",
        handler=handle_history,
        category="Information",
        description="Show conversation history",
        command_usage="/history [--json] - Display message history (--json for full JSON)",
    )

    tools_action = Action(
        name="tools",
        command="/tools",
        handler=handle_tools,
        category="Information",
        description="List available tools",
        command_usage="/tools - Show currently loaded tools",
    )

    conv_action = Action(
        name="conv",
        command="/conv",
        handler=handle_conv,
        category="Information",
        description="Show conversation manager status",
        command_usage="/conv - Display conversation manager configuration and statistics",
    )

    registry.register_action(history_action)
    registry.register_action(tools_action)
    registry.register_action(conv_action)
