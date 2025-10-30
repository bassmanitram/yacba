"""
YACBA Status Action for repl_toolkit.

Provides a comprehensive status summary of the current YACBA session.
"""

from repl_toolkit import Action, ActionContext, ActionRegistry
from rich.console import Console
from rich.panel import Panel


def handle_status(context: ActionContext) -> None:
    """Display current YACBA session status and statistics."""
    backend = context.backend
    args = context.args
    
    try:
        if args:
            print("The /status command takes no arguments.")
            return
        
        # Gather status information
        status_info = _gather_status_info(backend)
        
        # Format and display
        _display_status(status_info)
        
    except Exception as e:
        print(f"Error gathering status: {e}")


def _gather_status_info(backend) -> dict:
    """Gather comprehensive status information from backend."""
    status = {}
    
    # Get basic session info
    agent_proxy = backend.get_agent_proxy()
    config = backend.config
    
    # Session information
    status['session'] = {
        'model': config.model,
        'system_prompt_enabled': config.system_prompt is not None,
        'system_prompt_length': len(config.system_prompt) if config.system_prompt else 0,
        'session_id': config.session_id,
        'has_session': config.session_id is not None,
        'sessions_home': str(config.sessions_home) if config.sessions_home else None,
    }
    
    # Conversation information
    conversation_stats = backend.get_conversation_stats()
    status['conversation'] = {
        'total_messages': conversation_stats.get('message_count', 0),
        'user_messages': conversation_stats.get('user_messages', 0),
        'assistant_messages': conversation_stats.get('assistant_messages', 0),
        'manager_type': config.conversation_manager_type,
        'sliding_window_size': config.sliding_window_size,
        'preserve_recent': config.preserve_recent_messages,
    }
    
    # Tool information
    tool_names = backend.get_tool_names()
    status['tools'] = {
        'available_count': len(tool_names),
        'tool_names': tool_names,
    }
    
    # Configuration
    status['config'] = {
        'show_tool_use': config.show_tool_use,
        'response_prefix': config.response_prefix,
        'should_truncate_results': config.should_truncate_results,
        'emulate_system_prompt': config.emulate_system_prompt,
    }
    
    return status


def _display_status(status: dict) -> None:
    """Display formatted status information."""
    console = Console()
    
    # Create main content
    content = _build_status_content(status)
    
    # Display in a panel
    panel = Panel(
        content,
        title="🤖 YACBA Status",
        title_align="left",
        border_style="blue",
        padding=(1, 2)
    )
    
    console.print(panel)


def _build_status_content(status: dict) -> str:
    """Build the formatted status content."""
    lines = []
    
    # Session information
    session = status['session']
    lines.append(f"🤖 Model: {session['model']}")
    
    if session['system_prompt_enabled']:
        lines.append(f"📝 System Prompt: Enabled ({session['system_prompt_length']:,} chars)")
    else:
        lines.append("📝 System Prompt: Disabled")
    
    if session['has_session']:
        lines.append(f"💾 Session: {session['session_id']} (persistent)")
    else:
        lines.append("💾 Session: None (ephemeral)")
    
    lines.append("")  # Blank line
    
    # Conversation information
    conv = status['conversation']
    lines.append("💬 Conversation:")
    lines.append(f"   Messages: {conv['total_messages']}")
    lines.append(f"   Manager: {conv['manager_type']}")
    
    if conv['manager_type'] == 'sliding_window':
        lines.append(f"   Window size: {conv['sliding_window_size']}")
        lines.append(f"   Recent preserved: {conv['preserve_recent']}")
    
    lines.append("")  # Blank line
    
    # Tool information
    tools = status['tools']
    lines.append("🛠️  Tools:")
    lines.append(f"   Available: {tools['available_count']} tools")
    
    if tools['tool_names']:
        # Show first few tool names
        tool_preview = tools['tool_names'][:5]
        if len(tools['tool_names']) > 5:
            tool_preview.append(f"... and {len(tools['tool_names']) - 5} more")
        lines.append(f"   Tools: {', '.join(tool_preview)}")
    
    lines.append("")  # Blank line
    
    # Configuration
    config = status['config']
    lines.append("⚙️  Configuration:")
    lines.append(f"   Show tool use: {'Enabled' if config['show_tool_use'] else 'Disabled'}")
    lines.append(f"   Response prefix: {config['response_prefix'] or 'None'}")
    lines.append(f"   Result truncation: {'Enabled' if config['should_truncate_results'] else 'Disabled'}")
    lines.append(f"   Emulate system prompt: {'Enabled' if config['emulate_system_prompt'] else 'Disabled'}")
    
    return "\n".join(lines)


def register_status_actions(registry: ActionRegistry) -> None:
    """Register status display actions."""
    
    status_action = Action(
        name="status",
        command="/status",
        handler=handle_status,
        category="Information",
        description="Display comprehensive YACBA session status",
        command_usage="/status - Show session info, conversation state, tools, and configuration"
    )
    
    # Register aliases
    info_action = Action(
        name="info",
        command="/info",
        handler=handle_status,
        category="Information",
        description="Display comprehensive YACBA session status (alias for /status)",
        command_usage="/info - Show session info, conversation state, tools, and configuration"
    )
    
    stats_action = Action(
        name="stats",
        command="/stats",
        handler=handle_status,
        category="Information", 
        description="Display comprehensive YACBA session status (alias for /status)",
        command_usage="/stats - Show session info, conversation state, tools, and configuration"
    )
    
    registry.register_action(status_action)
    registry.register_action(info_action)
    registry.register_action(stats_action)