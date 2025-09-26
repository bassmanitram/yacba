"""
Prompt session management for YACBA CLI.

Handles the setup and configuration of interactive prompt sessions.
"""

from pathlib import Path
from loguru import logger
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.completion import Completer

def create_prompt_session(
    history_file: str = str(Path.home() / ".yacba" / "yacba_history"),
    completer: Completer = None
) -> PromptSession:
    """
    Create a configured prompt session for interactive input.

    Args:
        history_file: Path to history file
        completer: Tab completer instance (creates default if None)

    Returns:
        Configured PromptSession instance
    """
        # Ensure the .yacba directory exists
    history_path = Path(history_file)
    history_path.parent.mkdir(parents=True, exist_ok=True)

    history = FileHistory(history_file)
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

    Key Bindings:
    - Enter: Add new line (natural typing behavior)
    - Alt+Enter: Send message (works in all terminals)
    - Ctrl+J: Send message (alternative shortcut)

    Returns:
        KeyBindings instance with configured shortcuts
    """
    bindings = KeyBindings()

    @bindings.add("enter")
    def _(event):
        """Handle Enter key - add new line."""
        event.app.current_buffer.insert_text("\n")

    @bindings.add(Keys.Escape, "enter")
    def _(event):
        """Handle Alt+Enter - send message."""
        event.app.current_buffer.validate_and_handle()

    @bindings.add(Keys.ControlJ)
    def _(event):
        """Handle Ctrl+J - send message (alternative)."""
        event.app.current_buffer.validate_and_handle()

    return bindings
