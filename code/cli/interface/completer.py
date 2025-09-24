"""
Tab completion for YACBA CLI.

Provides intelligent completion for meta-commands and file paths.
"""

import re
from typing import List, Optional, Union

from prompt_toolkit.completion import Completer, PathCompleter, Completion
from prompt_toolkit.document import Document


class YacbaCompleter(Completer):
    """
    A context-aware completer that switches between meta-command and path completion.
    
    Provides intelligent tab completion for:
    - Meta-commands (e.g., /help, /session)
    - File paths in file() syntax
    - Command arguments where appropriate
    """
    
    def __init__(self, meta_commands: Optional[Union[List[str], dict]] = None):
        """
        Initialize the completer with path completion support.
        
        Args:
            meta_commands: List of meta-commands or command registry dict to complete.
                          Uses default commands if None.
        """
        self.path_completer = PathCompleter()
        
        # Handle different input types for meta_commands
        if meta_commands is None:
            # Default fallback commands
            self.meta_commands = [
                "/help",
                "/session", 
                "/clear",
                "/history",
                "/tools",
                "/exit",
                "/quit",
            ]
        elif isinstance(meta_commands, dict):
            # Extract commands from registry dict
            self.meta_commands = [cmd for cmd in meta_commands.keys() if cmd.startswith('/')]
        else:
            # Direct list of commands
            self.meta_commands = meta_commands

    def get_completions(self, document: Document, complete_event):
        """
        Generate completions based on the current input context.
        
        Args:
            document: Current document state
            complete_event: Completion event details
            
        Yields:
            Completion objects for matching items
        """
        text = document.text_before_cursor
        
        # Check for in-chat file upload syntax
        if self._is_file_completion_context(text):
            yield from self._get_file_completions(text, document, complete_event)
            return

        # Check for meta-command syntax
        if self._is_command_completion_context(text):
            yield from self._get_command_completions(text)

    def _is_file_completion_context(self, text: str) -> bool:
        """Check if we're in a file() completion context."""
        return bool(re.search(r"file\((['\"])(.*?)$", text))

    def _is_command_completion_context(self, text: str) -> bool:
        """Check if we're in a command completion context."""
        return text.startswith("/") and " " not in text

    def _get_file_completions(self, text: str, document: Document, complete_event):
        """Generate file path completions."""
        file_match = re.search(r"file\((['\"])(.*?)$", text)
        if not file_match:
            return

        path_prefix = file_match.group(2)
        # Avoid completing if quote is already in the path
        if file_match.group(1) in path_prefix:
            return

        path_doc = Document(text=path_prefix, cursor_position=len(path_prefix))
        yield from self.path_completer.get_completions(path_doc, complete_event)

    def _get_command_completions(self, text: str):
        """Generate meta-command completions."""
        for command in self.meta_commands:
            if command.startswith(text):
                yield Completion(
                    command,
                    start_position=-len(text),
                    display=command,
                    display_meta="meta-command",
                )

    def add_command(self, command: str):
        """
        Add a new command to the completion list.
        
        Args:
            command: Command to add (should start with '/')
        """
        if command not in self.meta_commands:
            self.meta_commands.append(command)

    def remove_command(self, command: str):
        """
        Remove a command from the completion list.
        
        Args:
            command: Command to remove
        """
        if command in self.meta_commands:
            self.meta_commands.remove(command)