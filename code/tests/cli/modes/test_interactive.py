"""
Simplified tests for cli.modes.interactive module.

Focused testing of core functionality without complex UI mocking.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from cli.modes.async_repl import AsyncREPL, run_async_repl
from cli.commands.registry import CommandRegistry


class TestChatInterfaceInit:
    """Test ChatInterface initialization."""

    def test_chat_interface_basic_init(self):
        """Test basic ChatInterface initialization."""
        mock_backend = Mock()
        
        with patch('cli.modes.interactive.create_prompt_session') as mock_create_session:
            mock_session = Mock()
            mock_session.app = Mock()
            mock_create_session.return_value = mock_session
            
            interface = AsyncREPL(mock_backend)
            
            assert interface.backend is mock_backend
            assert isinstance(interface.command_handler, CommandRegistry)
            assert interface.session is mock_session

    def test_chat_interface_with_custom_params(self):
        """Test ChatInterface with custom parameters."""
        mock_backend = Mock()
        mock_command_handler = Mock()
        mock_completer = Mock()
        
        with patch('cli.modes.interactive.create_prompt_session') as mock_create_session:
            mock_session = Mock()
            mock_session.app = Mock()
            mock_create_session.return_value = mock_session
            
            interface = AsyncREPL(
                backend=mock_backend,
                command_handler=mock_command_handler,
                completer=mock_completer
            )
            
            assert interface.backend is mock_backend
            assert interface.command_handler is mock_command_handler
            mock_create_session.assert_called_once_with(completer=mock_completer)


class TestShouldExit:
    """Test exit condition checking."""

    def setup_method(self):
        """Set up test fixtures."""
        mock_backend = Mock()
        with patch('cli.modes.interactive.create_prompt_session'):
            self.interface = AsyncREPL(mock_backend)

    def test_should_exit_commands(self):
        """Test various exit commands."""
        exit_commands = ["/exit", "/quit", "exit", "quit"]
        non_exit_commands = ["hello", "/help", "exit please", ""]
        
        for cmd in exit_commands:
            assert self.interface._should_exit(cmd) is True
        
        for cmd in non_exit_commands:
            assert self.interface._should_exit(cmd) is False

    def test_should_exit_case_insensitive(self):
        """Test exit commands are case insensitive."""
        commands = ["/EXIT", "/QUIT", "EXIT", "QUIT"]
        for cmd in commands:
            assert self.interface._should_exit(cmd) is True

    def test_should_exit_whitespace_handling(self):
        """Test exit commands handle whitespace."""
        commands = ["  /exit  ", "\t/quit\n", "  exit  "]
        for cmd in commands:
            assert self.interface._should_exit(cmd) is True


class TestChatLoopAsync:
    """Test the chat_loop_async wrapper function."""

    @pytest.mark.asyncio
    async def test_chat_loop_async_basic(self):
        """Test basic chat_loop_async functionality."""
        mock_backend = Mock()
        
        with patch('cli.modes.interactive.ChatInterface') as mock_interface_class:
            mock_interface = Mock()
            mock_interface.run = AsyncMock()
            mock_interface_class.return_value = mock_interface
            
            await run_async_repl(mock_backend)
            
            mock_interface_class.assert_called_once_with(mock_backend, None, None)
            mock_interface.run.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_chat_loop_async_with_params(self):
        """Test chat_loop_async with all parameters."""
        mock_backend = Mock()
        mock_command_handler = Mock()
        mock_completer = Mock()
        initial_message = "Hello"
        
        with patch('cli.modes.interactive.ChatInterface') as mock_interface_class:
            mock_interface = Mock()
            mock_interface.run = AsyncMock()
            mock_interface_class.return_value = mock_interface
            
            await run_async_repl(
                backend=mock_backend,
                command_handler=mock_command_handler,
                completer=mock_completer,
                initial_message=initial_message
            )
            
            mock_interface_class.assert_called_once_with(
                mock_backend, mock_command_handler, mock_completer
            )
            mock_interface.run.assert_called_once_with(initial_message)


class TestChatInterfaceCore:
    """Test core ChatInterface functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_backend = Mock()
        with patch('cli.modes.interactive.create_prompt_session'):
            self.interface = AsyncREPL(self.mock_backend)

    @pytest.mark.asyncio
    async def test_run_with_immediate_exit(self):
        """Test run method with immediate exit."""
        self.interface.session = Mock()
        self.interface.session.prompt_async = AsyncMock(return_value="/exit")
        
        # Should exit without calling backend
        await self.interface.run()

    @pytest.mark.asyncio
    async def test_run_handles_keyboard_interrupt(self):
        """Test run method handles KeyboardInterrupt gracefully."""
        self.interface.session = Mock()
        self.interface.session.prompt_async = AsyncMock(side_effect=KeyboardInterrupt)
        
        with patch('builtins.print'):
            # Should not raise exception
            await self.interface.run()

    @pytest.mark.asyncio
    async def test_run_handles_eof_error(self):
        """Test run method handles EOFError gracefully."""
        self.interface.session = Mock()
        self.interface.session.prompt_async = AsyncMock(side_effect=EOFError)
        
        with patch('builtins.print'):
            # Should not raise exception
            await self.interface.run()

    @pytest.mark.asyncio
    async def test_run_handles_general_exception(self):
        """Test run method handles general exceptions gracefully."""
        self.interface.session = Mock()
        self.interface.session.prompt_async = AsyncMock(side_effect=Exception("Test error"))
        
        with patch('builtins.print'):
            with patch('sys.stderr'):
                # Should not raise exception
                await self.interface.run()

    @pytest.mark.asyncio
    async def test_command_handling_flow(self):
        """Test command handling workflow."""
        self.interface.session = Mock()
        self.interface.session.prompt_async = AsyncMock(side_effect=["/help", "/exit"])
        self.interface.command_handler = Mock()
        self.interface.command_handler.handle_command = AsyncMock()
        
        await self.interface.run()
        
        self.interface.command_handler.handle_command.assert_called_once_with("/help")

    @pytest.mark.asyncio
    async def test_empty_input_handling(self):
        """Test that empty inputs are skipped."""
        self.interface.session = Mock()
        self.interface.session.prompt_async = AsyncMock(side_effect=["", "  ", "/exit"])
        
        with patch.object(self.interface, '_handle_chat_with_cancellation') as mock_handle:
            await self.interface.run()
            
            # Should not call handle for empty inputs
            mock_handle.assert_not_called()


class TestChatInterfaceIntegration:
    """Integration tests for ChatInterface."""

    @pytest.mark.asyncio
    async def test_interface_creation_and_basic_flow(self):
        """Test interface creation and basic operational flow."""
        mock_backend = Mock()
        
        with patch('cli.modes.interactive.create_prompt_session') as mock_create_session:
            mock_session = Mock()
            mock_session.app = Mock()
            mock_session.prompt_async = AsyncMock(return_value="/exit")
            mock_create_session.return_value = mock_session
            
            interface = AsyncREPL(mock_backend)
            
            # Should be able to run without errors
            await interface.run()
            
            # Session should have been called
            mock_session.prompt_async.assert_called()

    @pytest.mark.asyncio
    async def test_end_to_end_wrapper_usage(self):
        """Test using the wrapper function end-to-end."""
        mock_backend = Mock()
        
        with patch('cli.modes.interactive.ChatInterface') as mock_interface_class:
            # Create a mock interface that exits immediately
            mock_interface = Mock()
            mock_interface.run = AsyncMock()
            mock_interface_class.return_value = mock_interface
            
            # Should complete without errors
            await run_async_repl(mock_backend)
            
            # Interface should have been created and run
            mock_interface_class.assert_called_once()
            mock_interface.run.assert_called_once()

    def test_interface_attributes_and_structure(self):
        """Test that interface has expected attributes and structure."""
        mock_backend = Mock()
        
        with patch('cli.modes.interactive.create_prompt_session') as mock_create_session:
            mock_session = Mock()
            mock_session.app = Mock()
            mock_create_session.return_value = mock_session
            
            interface = AsyncREPL(mock_backend)
            
            # Should have all expected attributes
            assert hasattr(interface, 'backend')
            assert hasattr(interface, 'command_handler')
            assert hasattr(interface, 'session')
            assert hasattr(interface, 'main_app')
            assert hasattr(interface, 'prompt_string')
            
            # Should have expected methods
            assert callable(interface.run)
            assert callable(interface._should_exit)
            assert callable(interface._process_input)

    @pytest.mark.asyncio
    async def test_error_resilience(self):
        """Test that interface is resilient to various errors."""
        mock_backend = Mock()
        
        with patch('cli.modes.interactive.create_prompt_session') as mock_create_session:
            mock_session = Mock()
            mock_session.app = Mock()
            # Simulate session errors followed by successful exit
            mock_session.prompt_async = AsyncMock(side_effect=[
                Exception("Session error"),
                "/exit"
            ])
            mock_create_session.return_value = mock_session
            
            interface = AsyncREPL(mock_backend)
            
            with patch('builtins.print'):
                with patch('sys.stderr'):
                    # Should handle errors gracefully and continue
                    await interface.run()
                    
                    # Should have attempted to get input twice
                    assert mock_session.prompt_async.call_count == 2