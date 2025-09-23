"""
Prompt session management for YACBA CLI.

Handles the setup and configuration of interactive prompt sessions.
"""

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings

from .completer import YacbaCompleter


def create_prompt_session(
    history_file: str = ".yacba_history",
    completer: YacbaCompleter = None
) -> PromptSession:
    """
    Create a configured prompt session for interactive input.
    
    Args:
        history_file: Path to history file
        completer: Tab completer instance (creates default if None)
        
    Returns:
        Configured PromptSession instance
    """
    history = FileHistory(history_file)
    completer = completer or YacbaCompleter()
    key_bindings = _create_key_bindings()
    
    return PromptSession(
        history=history, 
        completer=completer,
        key_bindings=key_bindings,
        multiline=True
    )


def _create_key_bindings() -> KeyBindings:
    """
    Create key bindings for the prompt session.
    
    Returns:
        KeyBindings instance with configured shortcuts
    """
    bindings = KeyBindings()

    @bindings.add("enter")
    def _(event):
        """Handle Enter key - submit input."""
        event.app.current_buffer.validate_and_handle()

    @bindings.add("escape", "enter")
    def _(event):
        """Handle Alt+Enter - add new line."""
        event.app.current_buffer.insert_text("\n")

    return bindings
