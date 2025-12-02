"""
YACBA Status Action for repl_toolkit.

Provides a comprehensive status summary of the current YACBA session.
"""

from repl_toolkit import Action, ActionContext, ActionRegistry


def handle_status(context: ActionContext) -> None:
    """Display current YACBA session status and statistics."""
    backend = context.backend
    args = context.args
    printer = context.printer

    try:
        if args:
            printer("The /info command takes no arguments.")
            return

        # Gather status information
        status_info = _gather_status_info(backend)

        # Format and display
        _display_status(status_info, printer)

    except Exception as e:
        printer(f"Error gathering status: {e}")


def _gather_status_info(backend) -> dict:
    """Gather comprehensive status information from backend."""
    status = {}

    # Get basic session info
    config = backend.config

    # Session information
    status["session"] = {
        "model": config.model,
        "system_prompt_enabled": config.system_prompt is not None,
        "system_prompt_length": (
            len(config.system_prompt) if config.system_prompt else 0
        ),
        "session_id": config.session_id,
        "has_session": config.session_id is not None,
        "sessions_home": str(config.sessions_home) if config.sessions_home else None,
    }

    # Conversation information
    conversation_stats = backend.get_conversation_stats()
    status["conversation"] = {
        "total_messages": conversation_stats.get("message_count", 0),
        "user_messages": conversation_stats.get("user_messages", 0),
        "assistant_messages": conversation_stats.get("assistant_messages", 0),
        "manager_type": config.conversation_manager_type,
        "sliding_window_size": config.sliding_window_size,
        "preserve_recent": config.preserve_recent_messages,
    }

    # Tool information - get detailed info
    tool_details = backend.get_tool_details()
    status["tools"] = {
        "available_count": len(tool_details),
        "tool_details": tool_details,
    }

    # Configuration
    status["config"] = {
        "show_tool_use": config.show_tool_use,
        "response_prefix": config.response_prefix,
        "should_truncate_results": config.should_truncate_results,
        "emulate_system_prompt": config.emulate_system_prompt,
    }

    return status


def _display_status(status: dict, printer) -> None:
    """Display formatted status information."""
    content = _build_status_content(status)
    printer(content)


def _build_status_content(status: dict) -> str:
    """Build the formatted status content."""
    lines = []

    # Header
    lines.append("YACBA Status")
    lines.append("=" * 60)
    lines.append("")

    # Session information
    session = status["session"]
    lines.append("Session:")
    lines.append(f"  Model: {session['model']}")

    if session["system_prompt_enabled"]:
        lines.append(
            f"  System Prompt: Enabled ({session['system_prompt_length']:,} chars)"
        )
    else:
        lines.append("  System Prompt: Disabled")

    if session["has_session"]:
        lines.append(f"  Session: {session['session_id']} (persistent)")
    else:
        lines.append("  Session: None (ephemeral)")

    lines.append("")

    # Conversation information
    conv = status["conversation"]
    lines.append("Conversation:")
    lines.append(f"  Messages: {conv['total_messages']}")
    lines.append(f"  Manager: {conv['manager_type']}")

    if conv["manager_type"] == "sliding_window":
        lines.append(f"  Window size: {conv['sliding_window_size']}")
        lines.append(f"  Recent preserved: {conv['preserve_recent']}")

    lines.append("")

    # Tool information
    tools = status["tools"]
    lines.append(f"Tools: {tools['available_count']} available")

    if tools["tool_details"]:
        # Group by source
        by_source = {}
        for tool in tools["tool_details"]:
            source_type = tool.get("source_type", "unknown")
            source_id = tool.get("source_id", "")
            
            if source_type == "python":
                key = "Python Tools"
            elif source_type == "mcp":
                key = f"MCP: {source_id}"
            elif source_type == "a2a":
                key = f"A2A: {source_id}"
            else:
                key = "Other"
            
            if key not in by_source:
                by_source[key] = []
            by_source[key].append(tool["name"])
        
        # Display grouped tools with multi-line format
        for source_key in sorted(by_source.keys()):
            tool_names = sorted(by_source[source_key])
            lines.append(f"  {source_key}:")
            for tool_name in tool_names:
                lines.append(f"      {tool_name}")

    lines.append("")

    # Configuration
    config = status["config"]
    lines.append("Configuration:")
    lines.append(
        f"  Show tool use: {'Enabled' if config['show_tool_use'] else 'Disabled'}"
    )
    lines.append(f"  Response prefix: {config['response_prefix'] or 'None'}")
    lines.append(
        f"  Result truncation: {'Enabled' if config['should_truncate_results'] else 'Disabled'}"
    )
    lines.append(
        f"  Emulate system prompt: {'Enabled' if config['emulate_system_prompt'] else 'Disabled'}"
    )

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


def register_status_actions(registry: ActionRegistry) -> None:
    """Register status display action."""

    info_action = Action(
        name="info",
        command="/info",
        handler=handle_status,
        category="Information",
        description="Display comprehensive YACBA session status",
        command_usage="/info - Show session info, conversation state, tools, and configuration",
    )

    registry.register_action(info_action)
