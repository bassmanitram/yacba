"""
Session management actions for YACBA CLI.

Handles actions for session management:
- /session: Display/manage the current persisted session
- /clear: Clear the current conversation
"""

import re
from repl_toolkit import Action, ActionContext, ActionRegistry


def handle_session(context: ActionContext) -> None:
    """Handle the /session action."""
    args = context.args

    try:
        if not args:
            print("Session management not fully implemented yet.")
            print("Current session: default")
            return

        session_name = args[0]

        # Validate the session name format
        if not re.match(r"^[a-z][a-z0-9_-]*$", session_name):
            print(f"Invalid session name: '{session_name}'.")
            print(
                "Name must be lowercase, start with a letter, and contain "
                "only letters, numbers, '-', or '_'."
            )
            return

        print(f"Session switching to '{session_name}' not fully implemented yet.")

    except Exception as e:
        print(f"Unexpected error in /session: {e}")


def handle_clear(context: ActionContext) -> None:
    """Handle the /clear action."""
    backend = context.backend

    try:
        success = backend.clear_conversation()
        if success:
            print("Conversation messages cleared")
        else:
            print("Failed to clear conversation")
    except Exception as e:
        print(f"Unexpected error in /clear: {e}")


def register_session_actions(registry: ActionRegistry) -> None:
    """Register session management actions."""

    session_action = Action(
        name="session",
        command="/session",
        handler=handle_session,
        category="Session Management",
        description="Manage conversation sessions",
        command_usage="/session [name] - Show current session or switch to named session",
    )

    clear_action = Action(
        name="clear",
        command="/clear",
        handler=handle_clear,
        category="Session Management",
        description="Clear current conversation",
        command_usage="/clear - Clear conversation history",
    )

    registry.register_action(session_action)
    registry.register_action(clear_action)
