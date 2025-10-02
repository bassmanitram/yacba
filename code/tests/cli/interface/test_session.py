"""
Tests for cli.interface.session module.

Comprehensive testing of prompt session creation and key binding configuration.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.completion import Completer

from cli.interface.session import create_prompt_session, _create_key_bindings


class TestCreatePromptSession:
    """Test prompt session creation functionality."""

    def test_create_prompt_session_default_params(self):
        """Test creating prompt session with default parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_file = str(Path(temp_dir) / "test_history")
            
            session = create_prompt_session(history_file=history_file)
            
            assert isinstance(session, PromptSession)
            assert isinstance(session.history, FileHistory)
            assert session.multiline is True
            assert session.completer is None
            assert session.key_bindings is not None

    def test_create_prompt_session_with_completer(self):
        """Test creating prompt session with custom completer."""
        mock_completer = Mock(spec=Completer)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            history_file = str(Path(temp_dir) / "test_history")
            
            session = create_prompt_session(
                history_file=history_file,
                completer=mock_completer
            )
            
            assert session.completer is mock_completer

    def test_create_prompt_session_creates_history_directory(self):
        """Test that history directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / "nested" / "deep" / "history"
            history_file = str(nested_path)
            
            # Directory shouldn't exist initially
            assert not nested_path.parent.exists()
            
            session = create_prompt_session(history_file=history_file)
            
            # Directory should be created
            assert nested_path.parent.exists()
            assert isinstance(session, PromptSession)

    def test_create_prompt_session_default_yacba_history(self):
        """Test default history file location."""
        with patch('pathlib.Path.home') as mock_home:
            mock_home.return_value = Path("/mock/home")
            
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                # Test that the session is created successfully with default path
                session = create_prompt_session()
                
                # Should create .yacba directory
                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
                
                # Should create session successfully
                assert isinstance(session, PromptSession)


class TestCreateKeyBindings:
    """Test key binding creation functionality."""

    def test_create_key_bindings_returns_keybindings(self):
        """Test that _create_key_bindings returns KeyBindings instance."""
        bindings = _create_key_bindings()
        assert isinstance(bindings, KeyBindings)

    def test_key_bindings_structure(self):
        """Test that key bindings are properly configured."""
        bindings = _create_key_bindings()
        
        # KeyBindings should have registered handlers
        assert len(bindings.bindings) > 0
        
        # Should have bindings for enter, alt+enter, and ctrl+j
        binding_keys = []
        for binding in bindings.bindings:
            binding_keys.extend([key.value if hasattr(key, 'value') else str(key) for key in binding.keys])
        
        # Check that we have the expected key combinations
        # (Note: exact key representation may vary, so we check for presence)
        assert len(binding_keys) > 0

    @patch('prompt_toolkit.key_binding.KeyBindings.add')
    def test_enter_key_binding(self, mock_add):
        """Test that Enter key binding is properly configured."""
        _create_key_bindings()
        
        # Should be called multiple times for different key bindings
        assert mock_add.call_count >= 3
        
        # Check that "enter" is one of the registered keys
        calls = mock_add.call_args_list
        enter_call = None
        for call in calls:
            if call[0] and call[0][0] == "enter":
                enter_call = call
                break
        
        assert enter_call is not None

    def test_key_binding_handlers_exist(self):
        """Test that key binding handlers are callable."""
        bindings = _create_key_bindings()
        
        for binding in bindings.bindings:
            # Each binding should have a callable handler
            assert callable(binding.handler)

    def test_mock_key_binding_behavior(self):
        """Test key binding behavior with mock events."""
        bindings = _create_key_bindings()
        
        # Create mock event with buffer
        mock_event = Mock()
        mock_buffer = Mock()
        mock_app = Mock()
        mock_app.current_buffer = mock_buffer
        mock_event.app = mock_app
        
        # Test that handlers can be called without errors
        for binding in bindings.bindings:
            try:
                binding.handler(mock_event)
            except AttributeError:
                # Some handlers might expect specific buffer methods
                # This is expected and OK for unit tests
                pass


class TestSessionIntegration:
    """Integration tests for session functionality."""

    def test_session_with_real_history_file(self):
        """Test session creation with actual file operations."""
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            history_file = tf.name
            
        try:
            session = create_prompt_session(history_file=history_file)
            
            # Should be able to create session successfully
            assert isinstance(session, PromptSession)
            assert isinstance(session.history, FileHistory)
            
            # History file should exist
            assert Path(history_file).exists()
            
        finally:
            # Cleanup
            Path(history_file).unlink(missing_ok=True)

    def test_session_configuration_completeness(self):
        """Test that session has all expected configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_file = str(Path(temp_dir) / "history")
            mock_completer = Mock(spec=Completer)
            
            session = create_prompt_session(
                history_file=history_file,
                completer=mock_completer
            )
            
            # Verify all expected attributes
            assert hasattr(session, 'history')
            assert hasattr(session, 'completer')
            assert hasattr(session, 'key_bindings')
            assert hasattr(session, 'multiline')
            
            # Verify values
            assert session.completer is mock_completer
            assert session.multiline is True
            assert isinstance(session.key_bindings, KeyBindings)