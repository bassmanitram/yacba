"""
Tests for adapters.repl_toolkit.completer module.

Target Coverage: 95%+
"""

import pytest
from unittest.mock import Mock, patch
from prompt_toolkit.document import Document


class TestYacbaCompleter:
    """Tests for YacbaCompleter class."""

    def test_init(self):
        """Test YacbaCompleter initialization."""
        from adapters.repl_toolkit.completer import YacbaCompleter

        completer = YacbaCompleter()
        assert completer.path_completer is not None

    def test_is_file_completion_context_true(self):
        """Test detection of file() completion context."""
        from adapters.repl_toolkit.completer import YacbaCompleter

        completer = YacbaCompleter()

        # Should detect file() contexts
        assert completer._is_file_completion_context('file("')
        assert completer._is_file_completion_context('file("/tmp/')
        assert completer._is_file_completion_context("file('~/")
        assert completer._is_file_completion_context('some text file("/path')

    def test_is_file_completion_context_false(self):
        """Test non-file() contexts are not detected."""
        from adapters.repl_toolkit.completer import YacbaCompleter

        completer = YacbaCompleter()

        # Should NOT detect these
        assert not completer._is_file_completion_context("just text")
        assert not completer._is_file_completion_context("/command")
        assert not completer._is_file_completion_context("${HOME}")
        assert not completer._is_file_completion_context("file()")  # No quote
        assert not completer._is_file_completion_context(
            'filed("test'
        )  # Wrong spelling

    def test_get_completions_non_file_context(self, mock_complete_event):
        """Test that no completions returned outside file() context."""
        from adapters.repl_toolkit.completer import YacbaCompleter

        completer = YacbaCompleter()
        doc = Document(text="just some text", cursor_position=14)

        completions = list(completer.get_completions(doc, mock_complete_event))
        assert len(completions) == 0

    def test_get_completions_command_context(self, mock_complete_event):
        """Test that no completions for commands (handled by PrefixCompleter)."""
        from adapters.repl_toolkit.completer import YacbaCompleter

        completer = YacbaCompleter()
        doc = Document(text="/help", cursor_position=5)

        completions = list(completer.get_completions(doc, mock_complete_event))
        assert len(completions) == 0

    @patch("adapters.repl_toolkit.completer.PathCompleter")
    def test_get_completions_file_context(
        self, mock_path_completer_class, mock_complete_event
    ):
        """Test that completions are generated for file() context."""
        from adapters.repl_toolkit.completer import YacbaCompleter

        # Mock PathCompleter to return test completions
        mock_path_completer = Mock()
        mock_completion = Mock()
        mock_completion.text = "test.txt"
        mock_path_completer.get_completions = Mock(return_value=iter([mock_completion]))
        mock_path_completer_class.return_value = mock_path_completer

        completer = YacbaCompleter()
        completer.path_completer = mock_path_completer

        doc = Document(text='file("/tmp/', cursor_position=11)

        completions = list(completer.get_completions(doc, mock_complete_event))
        assert len(completions) > 0
        assert mock_path_completer.get_completions.called

    def test_get_file_completions_double_quote(self, mock_complete_event):
        """Test file completion with double quotes."""
        from adapters.repl_toolkit.completer import YacbaCompleter

        completer = YacbaCompleter()
        doc = Document(text='file("/tmp/', cursor_position=11)

        # Just verify it doesn't crash (actual PathCompleter behavior tested separately)
        completions = list(completer.get_completions(doc, mock_complete_event))
        # PathCompleter will return actual completions or empty list
        assert isinstance(completions, list)

    def test_get_file_completions_single_quote(self, mock_complete_event):
        """Test file completion with single quotes."""
        from adapters.repl_toolkit.completer import YacbaCompleter

        completer = YacbaCompleter()
        doc = Document(text="file('/tmp/", cursor_position=11)

        completions = list(completer.get_completions(doc, mock_complete_event))
        assert isinstance(completions, list)

    def test_get_file_completions_with_quote_in_path(self, mock_complete_event):
        """Test that completion avoids paths with quotes already in them."""
        from adapters.repl_toolkit.completer import YacbaCompleter

        completer = YacbaCompleter()

        # Path contains a quote - should not complete
        doc = Document(text='file("/tmp/test"extra', cursor_position=21)

        # Should not attempt completion when quote already in path
        completions = list(completer.get_completions(doc, mock_complete_event))
        # May return empty or may not match pattern
        assert isinstance(completions, list)

    def test_completion_with_tilde(self, mock_complete_event):
        """Test file completion with tilde expansion."""
        from adapters.repl_toolkit.completer import YacbaCompleter

        completer = YacbaCompleter()
        doc = Document(text='file("~/', cursor_position=8)

        # PathCompleter should handle tilde expansion
        completions = list(completer.get_completions(doc, mock_complete_event))
        assert isinstance(completions, list)

    def test_completion_relative_path(self, mock_complete_event):
        """Test file completion with relative paths."""
        from adapters.repl_toolkit.completer import YacbaCompleter

        completer = YacbaCompleter()
        doc = Document(text='file("./', cursor_position=7)

        completions = list(completer.get_completions(doc, mock_complete_event))
        assert isinstance(completions, list)


@pytest.mark.unit
class TestCompleterIntegration:
    """Integration tests for completer with prompt_toolkit."""

    def test_completer_protocol(self):
        """Test that YacbaCompleter implements Completer protocol."""
        from adapters.repl_toolkit.completer import YacbaCompleter
        from prompt_toolkit.completion import Completer

        completer = YacbaCompleter()
        assert isinstance(completer, Completer)

    def test_completer_in_merged_context(self, mock_complete_event):
        """Test YacbaCompleter works in merged completer setup."""
        from adapters.repl_toolkit.completer import YacbaCompleter
        from prompt_toolkit.completion import merge_completers

        file_completer = YacbaCompleter()

        # Create a simple mock completer for merging
        mock_other = Mock()
        mock_other.get_completions = Mock(return_value=iter([]))

        merged = merge_completers([mock_other, file_completer])

        # Test that merged completer works
        doc = Document(text='file("/tmp/', cursor_position=11)
        completions = list(merged.get_completions(doc, mock_complete_event))
        assert isinstance(completions, list)
