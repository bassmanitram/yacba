"""
Tests for adapters.cli.commands.session_commands module.

Tests for session management commands that work with the engine adapter.
"""

import pytest
import re
from unittest.mock import Mock, patch
from typing import List

from adapters.cli.commands.session_commands import SessionCommands
from cli.commands.base_command import CommandError


class TestSessionCommandsInit:
    """Test SessionCommands initialization."""

    def test_session_commands_initialization(self):
        """Test SessionCommands initialization."""
        mock_registry = Mock()
        mock_engine = Mock()
        session_cmd = SessionCommands(mock_registry, mock_engine)
        
        assert session_cmd.registry is mock_registry
        assert session_cmd.engine is mock_engine
        assert session_cmd._command_name == "session"


class TestSessionCommandsHandling:
    """Test session command handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = Mock()
        self.mock_engine = Mock()
        self.session_cmd = SessionCommands(self.mock_registry, self.mock_engine)

    @pytest.mark.asyncio
    async def test_handle_session_command(self):
        """Test handling /session command."""
        with patch.object(self.session_cmd, '_handle_session') as mock_handle_session:
            await self.session_cmd.handle_command('/session', ['test'])
            mock_handle_session.assert_called_once_with(['test'])

    @pytest.mark.asyncio
    async def test_handle_clear_command(self):
        """Test handling /clear command."""
        with patch.object(self.session_cmd, '_clear_session') as mock_clear_session:
            await self.session_cmd.handle_command('/clear', [])
            mock_clear_session.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_handle_unknown_command(self):
        """Test handling unknown command."""
        with patch.object(self.session_cmd, 'print_error') as mock_print_error:
            await self.session_cmd.handle_command('/unknown', [])
            mock_print_error.assert_called_once_with("Unknown info command: /unknown")

    @pytest.mark.asyncio
    async def test_handle_command_error_exception(self):
        """Test handling CommandError exception."""
        with patch.object(self.session_cmd, '_handle_session', side_effect=CommandError("Test error")):
            with patch.object(self.session_cmd, 'print_error') as mock_print_error:
                await self.session_cmd.handle_command('/session', [])
                mock_print_error.assert_called_once_with("Test error")

    @pytest.mark.asyncio
    async def test_handle_general_exception(self):
        """Test handling general exception."""
        with patch.object(self.session_cmd, '_handle_session', side_effect=Exception("General error")):
            with patch.object(self.session_cmd, 'print_error') as mock_print_error:
                await self.session_cmd.handle_command('/session', [])
                mock_print_error.assert_called_once_with("Unexpected error in /session: General error")


class TestHandleSessionCommand:
    """Test the _handle_session method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = Mock()
        self.mock_engine = Mock()
        self.mock_session_manager = Mock()
        self.mock_engine.session_manager = self.mock_session_manager
        self.session_cmd = SessionCommands(self.mock_registry, self.mock_engine)

    @pytest.mark.asyncio
    async def test_handle_session_no_args_with_sessions(self):
        """Test session command with no args when sessions exist."""
        self.mock_session_manager.list_sessions.return_value = ['session1', 'session2', 'session3']
        self.mock_session_manager.session_id = 'session2'
        
        with patch('builtins.print') as mock_print:
            await self.session_cmd._handle_session([])
            
            mock_print.assert_any_call("Available sessions:")
            mock_print.assert_any_call("    session1")  # Adjust to actual output
            mock_print.assert_any_call("  * session2")  # Current session marked with *
            mock_print.assert_any_call("    session3")

    @pytest.mark.asyncio
    async def test_handle_session_no_args_no_sessions(self):
        """Test session command with no args when no sessions exist."""
        self.mock_session_manager.list_sessions.return_value = []
        
        with patch('builtins.print') as mock_print:
            await self.session_cmd._handle_session([])
            
            mock_print.assert_called_once_with("No saved sessions found.")

    @pytest.mark.asyncio
    async def test_handle_session_invalid_name_format(self):
        """Test session command with invalid session name format."""
        invalid_names = ['Session1', '1session', 'session-name!', 'session name']
        
        for invalid_name in invalid_names:
            with patch('builtins.print') as mock_print:
                await self.session_cmd._handle_session([invalid_name])
                
                mock_print.assert_any_call(f"Invalid session name: '{invalid_name}'.")
                mock_print.assert_any_call("Name must be lowercase, start with a letter, and contain only letters, numbers, '-', or '_'.")

    @pytest.mark.asyncio
    async def test_handle_session_valid_name_formats(self):
        """Test session command with valid session name formats."""
        valid_names = ['session1', 'my-session', 'my_session', 'a', 'test123']
        
        for valid_name in valid_names:
            self.mock_session_manager.session_id = 'other'  # Different from target
            
            with patch('builtins.print') as mock_print:
                await self.session_cmd._handle_session([valid_name])
                
                self.mock_session_manager.set_active_session.assert_called_with(valid_name)
                mock_print.assert_called_with(f"Switched to session '{valid_name}'.")

    @pytest.mark.asyncio
    async def test_handle_session_already_active(self):
        """Test session command when already in requested session."""
        session_name = 'current-session'
        self.mock_session_manager.session_id = session_name
        
        with patch('builtins.print') as mock_print:
            await self.session_cmd._handle_session([session_name])
            
            mock_print.assert_called_once_with(f"Already in session '{session_name}'.")
            self.mock_session_manager.set_active_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_session_switch_to_new(self):
        """Test session command switching to new session."""
        session_name = 'new-session'
        self.mock_session_manager.session_id = 'old-session'
        
        with patch('builtins.print') as mock_print:
            await self.session_cmd._handle_session([session_name])
            
            self.mock_session_manager.set_active_session.assert_called_once_with(session_name)
            mock_print.assert_called_once_with(f"Switched to session '{session_name}'.")


class TestSessionNameValidation:
    """Test session name validation logic."""

    def test_valid_session_names(self):
        """Test valid session name patterns."""
        valid_names = [
            'a',
            'session',
            'session1',
            'my-session',
            'my_session',
            'test123',
            'a-b-c',
            'a_b_c',
            'session-with-many-parts',
            'session_with_many_parts'
        ]
        
        pattern = r"^[a-z][a-z0-9_-]*$"
        
        for name in valid_names:
            assert re.match(pattern, name), f"'{name}' should be valid"

    def test_invalid_session_names(self):
        """Test invalid session name patterns."""
        invalid_names = [
            '',  # Empty
            '1session',  # Starts with number
            'Session',  # Capital letter
            'session name',  # Space
            'session!',  # Special character
            'session@test',  # @ symbol
            'session.test',  # Dot
            '-session',  # Starts with dash
            '_session',  # Starts with underscore
            'session-',  # Ends with dash (actually valid in current regex)
            'ALLCAPS'  # All capitals
        ]
        
        pattern = r"^[a-z][a-z0-9_-]*$"
        
        for name in invalid_names:
            if name == 'session-':  # This is actually valid
                continue
            assert not re.match(pattern, name), f"'{name}' should be invalid"


class TestClearSessionCommand:
    """Test the _clear_session method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = Mock()
        self.mock_engine = Mock()
        self.mock_session_manager = Mock()
        self.mock_engine.session_manager = self.mock_session_manager
        self.session_cmd = SessionCommands(self.mock_registry, self.mock_engine)

    @pytest.mark.asyncio
    async def test_clear_session(self):
        """Test clearing session."""
        with patch('builtins.print') as mock_print:
            await self.session_cmd._clear_session([])
            
            self.mock_session_manager.clear.assert_called_once()
            mock_print.assert_called_once_with("Conversation messages cleared")

    @pytest.mark.asyncio
    async def test_clear_session_with_args(self):
        """Test clearing session with args (should still work)."""
        with patch('builtins.print') as mock_print:
            await self.session_cmd._clear_session(['ignored', 'args'])
            
            self.mock_session_manager.clear.assert_called_once()
            mock_print.assert_called_once_with("Conversation messages cleared")


class TestSessionCommandsIntegration:
    """Integration tests for SessionCommands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = Mock()
        self.mock_engine = Mock()
        self.mock_session_manager = Mock()
        self.mock_engine.session_manager = self.mock_session_manager
        self.session_cmd = SessionCommands(self.mock_registry, self.mock_engine)

    @pytest.mark.asyncio
    async def test_full_session_workflow(self):
        """Test complete session management workflow."""
        # 1. List sessions when none exist
        self.mock_session_manager.list_sessions.return_value = []
        
        with patch('builtins.print') as mock_print:
            await self.session_cmd._handle_session([])
            mock_print.assert_called_with("No saved sessions found.")

        # 2. Switch to new session
        self.mock_session_manager.session_id = None
        
        with patch('builtins.print') as mock_print:
            await self.session_cmd._handle_session(['newsession'])
            
            self.mock_session_manager.set_active_session.assert_called_with('newsession')
            mock_print.assert_called_with("Switched to session 'newsession'.")

        # 3. List sessions with current session
        self.mock_session_manager.list_sessions.return_value = ['newsession', 'othersession']
        self.mock_session_manager.session_id = 'newsession'
        
        with patch('builtins.print') as mock_print:
            await self.session_cmd._handle_session([])
            
            mock_print.assert_any_call("Available sessions:")
            mock_print.assert_any_call("  * newsession")
            mock_print.assert_any_call("    othersession")  # Adjust to actual output

        # 4. Clear session
        with patch('builtins.print') as mock_print:
            await self.session_cmd._clear_session([])
            
            self.mock_session_manager.clear.assert_called_once()
            mock_print.assert_called_with("Conversation messages cleared")

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Test error handling in session commands."""
        # Test session manager exception
        self.mock_session_manager.list_sessions.side_effect = Exception("Session error")
        
        with pytest.raises(Exception):
            await self.session_cmd._handle_session([])

        # Test clear session exception
        self.mock_session_manager.clear.side_effect = Exception("Clear error")
        
        with pytest.raises(Exception):
            await self.session_cmd._clear_session([])

    @pytest.mark.asyncio
    async def test_session_validation_edge_cases(self):
        """Test edge cases in session name validation."""
        edge_cases = [
            ('a', True),  # Single character
            ('z9', True),  # Letter + number
            ('test-test', True),  # With dash
            ('test_test', True),  # With underscore
            ('9test', False),  # Starts with number
            ('Test', False),  # Capital letter
            ('test test', False),  # Space
            ('', False)  # Empty string
        ]
        
        for session_name, should_be_valid in edge_cases:
            if should_be_valid:
                # Should call set_active_session
                self.mock_session_manager.session_id = 'other'
                with patch('builtins.print'):
                    await self.session_cmd._handle_session([session_name])
                    self.mock_session_manager.set_active_session.assert_called_with(session_name)
            else:
                # Should print error
                with patch('builtins.print') as mock_print:
                    await self.session_cmd._handle_session([session_name])
                    if session_name:  # Non-empty invalid names
                        mock_print.assert_any_call(f"Invalid session name: '{session_name}'.")
            
            # Reset mock
            self.mock_session_manager.reset_mock()