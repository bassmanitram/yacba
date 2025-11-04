"""
Tab completion for YACBA CLI.

Provides intelligent completion for file paths in file() syntax.
Command completion is handled by repl_toolkit's PrefixCompleter.
Shell expansion is handled by repl_toolkit's ShellExpansionCompleter.
"""

import re

from prompt_toolkit.completion import Completer, PathCompleter
from prompt_toolkit.document import Document


class YacbaCompleter(Completer):
    """
    File path completer for file() syntax.

    This completer handles only file path completion within file() function calls.
    Meta-commands (/) are handled by repl_toolkit's PrefixCompleter.
    Shell expansion (${VAR} and $(cmd)) is handled by repl_toolkit's ShellExpansionCompleter.

    Example:
        file("~/Doc<TAB>  ->  file("~/Documents/
        file('/etc/pas<TAB>  ->  file('/etc/passwd
    """

    def __init__(self):
        """Initialize the file path completer."""
        self.path_completer = PathCompleter(expanduser=True)

    def get_completions(self, document: Document, complete_event):
        """
        Generate file path completions for file() syntax.

        Args:
            document: Current document state
            complete_event: Completion event details

        Yields:
            Completion objects for matching file paths
        """
        text = document.text_before_cursor

        # Only handle file() completion
        if self._is_file_completion_context(text):
            yield from self._get_file_completions(text, document, complete_event)

    def _is_file_completion_context(self, text: str) -> bool:
        """
        Check if we're in a file() completion context.

        Args:
            text: Text before cursor

        Returns:
            True if cursor is within file() function call
        """
        return bool(re.search(r"file\((['\"])(.*?)$", text))

    def _get_file_completions(self, text: str, document: Document, complete_event):
        """
        Generate file path completions within file() syntax.

        Args:
            text: Text before cursor
            document: Current document
            complete_event: Completion event

        Yields:
            Path completion objects
        """
        file_match = re.search(r"file\((['\"])(.*?)$", text)
        if not file_match:
            return

        quote_char = file_match.group(1)
        path_prefix = file_match.group(2)

        # Avoid completing if quote is already in the path
        if quote_char in path_prefix:
            return

        # Create a document with just the path portion
        path_doc = Document(text=path_prefix, cursor_position=len(path_prefix))
        yield from self.path_completer.get_completions(path_doc, complete_event)
