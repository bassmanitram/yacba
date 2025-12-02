"""
Session management actions for YACBA CLI.

Handles actions for session management:
- clear: Clear the current conversation
"""

from repl_toolkit import Action, ActionContext, ActionRegistry


def handle_clear(context: ActionContext) -> None:
    """Handle the clear action.
    
    Clears conversation messages and recreates session start tag.
    """
    backend = context.backend
    printer = context.printer

    try:
        success = backend.clear_conversation()
        if success:
            printer("Conversation messages cleared")
        else:
            printer("Failed to clear conversation")
    except Exception as e:
        printer(f"Unexpected error in /clear: {e}")


def register_session_actions(registry: ActionRegistry) -> None:
    """Register session management actions."""

    clear_action = Action(
        name="clear",
        command="/clear",
        handler=handle_clear,
        category="Session Management",
        description="Clear current conversation",
        command_usage="/clear - Clear conversation history",
    )

    registry.register_action(clear_action)
