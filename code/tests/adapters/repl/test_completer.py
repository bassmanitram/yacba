"""
Tests for adapters.repl.completer module.

Tests for tab completion functionality in YACBA CLI.
"""

import pytest
from unittest.mock import Mock, patch
from prompt_toolkit.document import Document
from prompt_toolkit.completion import Completion
from prompt_toolkit.formatted_text import to_plain_text

from adapters.repl.completer import YacbaCompleter


class TestYacbaCompleterInit:
    """Test YacbaCompleter initialization."""

    def test_completer_initialization_default(self):
        """Test completer initialization with default commands."""
        completer = YacbaCompleter()
        
        assert completer.meta_commands == []
        assert hasattr(completer, 'path_completer')

    def test_completer_initialization_with_commands_list(self):
        """Test completer initialization with command list."""
        commands = ['/help', '/session', '/history']
        completer = YacbaCompleter(commands)
        
        assert completer.meta_commands == commands

    def test_completer_initialization_with_commands_dict(self):
        """Test completer initialization with command dict."""
        commands = {'/help': {}, '/session': {}}
        completer = YacbaCompleter(commands)
        
        assert completer.meta_commands == commands


class TestYacbaCompleterContextDetection:
    """Test context detection for different completion types."""

    def setup_method(self):
        """Set up test fixtures."""
        self.commands = ['/help', '/session', '/history', '/tools']
        self.completer = YacbaCompleter(self.commands)

    def test_is_file_completion_context_true(self):
        """Test file completion context detection - positive cases."""
        file_contexts = [
            'file("path',
            "file('path",
            'Please analyze file("./test',
            "Can you check file('/home/user",
            'file("',
            "file(''"
        ]
        
        for context in file_contexts:
            assert self.completer._is_file_completion_context(context) is True

    def test_is_file_completion_context_false(self):
        """Test file completion context detection - negative cases."""
        non_file_contexts = [
            '/help',
            'file(path)',  # Missing quotes
            'regular text',
            'file without parentheses',
            ''
        ]
        
        for context in non_file_contexts:
            result = self.completer._is_file_completion_context(context)
            assert result is False

    def test_is_file_completion_context_edge_cases(self):
        """Test edge cases for file completion context."""
        # The regex actually matches file("path") because it looks for file('quote')content$
        # So file("path") matches with content being "path" 
        edge_cases = [
            ('file("path")', True),  # This actually matches the regex
        ]
        
        for context, expected in edge_cases:
            result = self.completer._is_file_completion_context(context)
            assert result is expected, f"'{context}' should return {expected}"

    def test_is_command_completion_context_true(self):
        """Test command completion context detection - positive cases."""
        command_contexts = [
            '/',
            '/h',
            '/help',
            '/session',
            '/unknowncommand'
        ]
        
        for context in command_contexts:
            assert self.completer._is_command_completion_context(context) is True

    def test_is_command_completion_context_false(self):
        """Test command completion context detection - negative cases."""
        non_command_contexts = [
            '/help arg',  # Has space
            'help',  # No leading slash
            'regular text',
            'file("/path")',
            '/command with space',
            ''
        ]
        
        for context in non_command_contexts:
            assert self.completer._is_command_completion_context(context) is False


class TestYacbaCompleterFileCompletion:
    """Test file completion functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.completer = YacbaCompleter([])

    def test_get_file_completions_with_path(self):
        """Test file completions with path."""
        text = 'file("./test'
        document = Mock()
        complete_event = Mock()
        
        # Mock path completer
        mock_completion = Completion("test.txt", start_position=0)
        with patch.object(self.completer.path_completer, 'get_completions', return_value=[mock_completion]):
            completions = list(self.completer._get_file_completions(text, document, complete_event))
            
            assert len(completions) == 1
            assert completions[0] == mock_completion

    def test_get_file_completions_no_match(self):
        """Test file completions when no file() pattern matches."""
        text = 'regular text'
        document = Mock()
        complete_event = Mock()
        
        completions = list(self.completer._get_file_completions(text, document, complete_event))
        assert len(completions) == 0

    def test_get_file_completions_quote_in_path(self):
        """Test file completions when quote is in path (should not complete)."""
        text = 'file("path"with"quote'
        document = Mock()
        complete_event = Mock()
        
        completions = list(self.completer._get_file_completions(text, document, complete_event))
        assert len(completions) == 0

    def test_get_file_completions_single_quotes(self):
        """Test file completions with single quotes."""
        text = "file('./test"
        document = Mock()
        complete_event = Mock()
        
        mock_completion = Completion("test.py", start_position=0)
        with patch.object(self.completer.path_completer, 'get_completions', return_value=[mock_completion]):
            completions = list(self.completer._get_file_completions(text, document, complete_event))
            
            assert len(completions) == 1
            assert completions[0] == mock_completion


class TestYacbaCompleterCommandCompletion:
    """Test command completion functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.commands = ['/help', '/session', '/history', '/tools', '/clear']
        self.completer = YacbaCompleter(self.commands)

    def test_get_command_completions_partial_match(self):
        """Test command completions with partial match."""
        text = '/h'
        
        completions = list(self.completer._get_command_completions(text))
        
        # Should match /help and /history
        completion_texts = [c.text for c in completions]
        assert '/help' in completion_texts
        assert '/history' in completion_texts
        assert '/session' not in completion_texts  # Shouldn't match
        
        # Check completion properties
        for completion in completions:
            assert completion.start_position == -len(text)
            # display_meta in prompt_toolkit becomes a FormattedText
            # Convert to plain text for comparison
            assert to_plain_text(completion.display_meta) == "meta-command"

    def test_get_command_completions_exact_match(self):
        """Test command completions with exact match."""
        text = '/help'
        
        completions = list(self.completer._get_command_completions(text))
        
        # Should match /help exactly
        completion_texts = [c.text for c in completions]
        assert '/help' in completion_texts
        assert len([c for c in completion_texts if c == '/help']) == 1

    def test_get_command_completions_no_match(self):
        """Test command completions with no match."""
        text = '/xyz'
        
        completions = list(self.completer._get_command_completions(text))
        
        assert len(completions) == 0

    def test_get_command_completions_root_slash(self):
        """Test command completions starting with just slash."""
        text = '/'
        
        completions = list(self.completer._get_command_completions(text))
        
        # Should match all commands
        completion_texts = [c.text for c in completions]
        assert len(completions) == len(self.commands)
        for cmd in self.commands:
            assert cmd in completion_texts

    def test_get_command_completions_case_sensitive(self):
        """Test that command completions are case sensitive."""
        text = '/H'
        
        completions = list(self.completer._get_command_completions(text))
        
        # Should not match /help (lowercase)
        assert len(completions) == 0


class TestYacbaCompleterMainInterface:
    """Test main completion interface."""

    def setup_method(self):
        """Set up test fixtures."""
        self.commands = ['/help', '/session', '/history']
        self.completer = YacbaCompleter(self.commands)

    def test_get_completions_command_context(self):
        """Test main completion interface for command context."""
        document = Document(text='/h', cursor_position=2)
        complete_event = Mock()
        
        with patch.object(self.completer, '_get_command_completions') as mock_cmd_completions:
            mock_cmd_completions.return_value = [Completion('/help', start_position=-2)]
            
            completions = list(self.completer.get_completions(document, complete_event))
            
            mock_cmd_completions.assert_called_once_with('/h')
            assert len(completions) == 1

    def test_get_completions_file_context(self):
        """Test main completion interface for file context."""
        document = Document(text='file("./test', cursor_position=12)
        complete_event = Mock()
        
        with patch.object(self.completer, '_get_file_completions') as mock_file_completions:
            mock_file_completions.return_value = [Completion('test.txt', start_position=0)]
            
            completions = list(self.completer.get_completions(document, complete_event))
            
            # The actual text passed should be the text before cursor
            mock_file_completions.assert_called_once_with('file("./test', document, complete_event)
            assert len(completions) == 1

    def test_get_completions_no_context(self):
        """Test main completion interface with no special context."""
        document = Document(text='regular text', cursor_position=12)
        complete_event = Mock()
        
        completions = list(self.completer.get_completions(document, complete_event))
        
        # Should return no completions for regular text
        assert len(completions) == 0

    def test_get_completions_mixed_text_with_command(self):
        """Test completion with mixed text containing command."""
        # This test is tricky - the text "Please use /h" with cursor at position 13
        # should only trigger command completion if the cursor is within the command part
        document = Document(text='Please use /h', cursor_position=13)
        complete_event = Mock()
        
        # The implementation uses text_before_cursor which would be "Please use /h"
        # This doesn't start with "/" so won't trigger command completion
        completions = list(self.completer.get_completions(document, complete_event))
        
        # Should return no completions because text doesn't start with /
        assert len(completions) == 0


class TestYacbaCompleterCommandManagement:
    """Test command addition and removal."""

    def setup_method(self):
        """Set up test fixtures."""
        self.initial_commands = ['/help', '/session']
        self.completer = YacbaCompleter(self.initial_commands)

    def test_add_command(self):
        """Test adding a new command."""
        new_command = '/newcommand'
        self.completer.add_command(new_command)
        
        assert new_command in self.completer.meta_commands
        
        # Should now complete the new command
        completions = list(self.completer._get_command_completions('/new'))
        completion_texts = [c.text for c in completions]
        assert new_command in completion_texts

    def test_add_command_duplicate(self):
        """Test adding duplicate command (should not add twice)."""
        existing_command = '/help'
        original_count = len(self.completer.meta_commands)
        
        self.completer.add_command(existing_command)
        
        # Should not increase count
        assert len(self.completer.meta_commands) == original_count

    def test_remove_command(self):
        """Test removing an existing command."""
        command_to_remove = '/help'
        
        # Verify it exists first
        assert command_to_remove in self.completer.meta_commands
        
        self.completer.remove_command(command_to_remove)
        
        assert command_to_remove not in self.completer.meta_commands
        
        # Should no longer complete the removed command
        completions = list(self.completer._get_command_completions('/h'))
        completion_texts = [c.text for c in completions]
        assert command_to_remove not in completion_texts

    def test_remove_command_nonexistent(self):
        """Test removing non-existent command (should not error)."""
        nonexistent_command = '/nonexistent'
        original_count = len(self.completer.meta_commands)
        
        # Should not raise error
        self.completer.remove_command(nonexistent_command)
        
        # Should not change count
        assert len(self.completer.meta_commands) == original_count


class TestYacbaCompleterIntegration:
    """Integration tests for YacbaCompleter."""

    def test_realistic_completion_workflow(self):
        """Test realistic completion workflow."""
        commands = ['/help', '/session', '/history', '/tools', '/clear']
        completer = YacbaCompleter(commands)
        
        # 1. Complete command
        document = Document(text='/s', cursor_position=2)
        completions = list(completer.get_completions(document, Mock()))
        completion_texts = [c.text for c in completions]
        assert '/session' in completion_texts
        
        # 2. Complete file path
        document = Document(text='file("./te', cursor_position=10)
        with patch.object(completer.path_completer, 'get_completions') as mock_path:
            mock_path.return_value = [Completion('test.txt', start_position=0)]
            completions = list(completer.get_completions(document, Mock()))
            assert len(completions) == 1
        
        # 3. No completion for regular text
        document = Document(text='regular message', cursor_position=15)
        completions = list(completer.get_completions(document, Mock()))
        assert len(completions) == 0

    def test_edge_cases(self):
        """Test edge cases in completion."""
        completer = YacbaCompleter(['/help'])
        
        # Empty document
        document = Document(text='', cursor_position=0)
        completions = list(completer.get_completions(document, Mock()))
        assert len(completions) == 0
        
        # Just slash
        document = Document(text='/', cursor_position=1)
        completions = list(completer.get_completions(document, Mock()))
        completion_texts = [c.text for c in completions]
        assert '/help' in completion_texts

    def test_complex_file_patterns(self):
        """Test complex file completion patterns."""
        completer = YacbaCompleter([])
        
        complex_patterns = [
            'Please analyze file("./src/main',
            'Check file("/home/user/docs/report',
            "Open file('./config",
        ]
        
        for pattern in complex_patterns:
            document = Document(text=pattern, cursor_position=len(pattern))
            # Should detect as file completion context
            assert completer._is_file_completion_context(pattern) is True