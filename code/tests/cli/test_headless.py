"""
Simplified tests for cli.headless module.

Focused testing of core functionality without complex stderr mocking.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, call

from cli.headless import run_headless


class TestRunHeadlessModeCore:
    """Test core headless mode functionality."""

    @pytest.mark.asyncio
    async def test_run_headless_mode_initial_message_calls_backend(self):
        """Test that initial message is sent to backend."""
        mock_backend = Mock()
        mock_backend.handle_input = AsyncMock()
        
        with patch('builtins.input', side_effect=EOFError):
            await run_headless(
                backend=mock_backend,
                initial_message="Test initial message",
                verbose=False  # Disable verbose to avoid stderr complexity
            )
            
            mock_backend.handle_input.assert_called_once_with("Test initial message")

    @pytest.mark.asyncio
    async def test_run_headless_mode_no_initial_message(self):
        """Test headless mode without initial message."""
        mock_backend = Mock()
        mock_backend.handle_input = AsyncMock()
        
        with patch('builtins.input', side_effect=EOFError):
            await run_headless(backend=mock_backend, verbose=False)
            
            # Should not call backend with initial message
            mock_backend.handle_input.assert_not_called()

    @pytest.mark.asyncio
    async def test_single_message_with_send(self):
        """Test processing single message with /send command."""
        mock_backend = Mock()
        mock_backend.handle_input = AsyncMock()
        
        input_sequence = ["Hello world", "/send", EOFError]
        
        with patch('builtins.input', side_effect=input_sequence):
            await run_headless(backend=mock_backend, verbose=False)
            
            mock_backend.handle_input.assert_called_once_with("Hello world")

    @pytest.mark.asyncio
    async def test_multiline_message_with_send(self):
        """Test processing multiple lines with /send command."""
        mock_backend = Mock()
        mock_backend.handle_input = AsyncMock()
        
        input_sequence = [
            "Line 1",
            "Line 2", 
            "Line 3",
            "/send",
            EOFError
        ]
        
        with patch('builtins.input', side_effect=input_sequence):
            await run_headless(backend=mock_backend, verbose=False)
            
            expected_input = "Line 1Line 2Line 3"
            mock_backend.handle_input.assert_called_once_with(expected_input)

    @pytest.mark.asyncio
    async def test_multiple_turns(self):
        """Test multiple conversation turns."""
        mock_backend = Mock()
        mock_backend.handle_input = AsyncMock()
        
        input_sequence = [
            "First message",
            "/send",
            "Second message", 
            "/send",
            EOFError
        ]
        
        with patch('builtins.input', side_effect=input_sequence):
            await run_headless(backend=mock_backend, verbose=False)
            
            assert mock_backend.handle_input.call_count == 2
            mock_backend.handle_input.assert_has_calls([
                call("First message"),
                call("Second message")
            ])

    @pytest.mark.asyncio
    async def test_eof_with_buffered_content(self):
        """Test EOF with content in buffer."""
        mock_backend = Mock()
        mock_backend.handle_input = AsyncMock()
        
        input_sequence = [
            "Buffered content",
            EOFError  # EOF without /send
        ]
        
        with patch('builtins.input', side_effect=input_sequence):
            await run_headless(backend=mock_backend, verbose=False)
            
            # Should send buffered content before exiting
            mock_backend.handle_input.assert_called_once_with("Buffered content")

    @pytest.mark.asyncio
    async def test_empty_send_skipped(self):
        """Test that empty /send commands are skipped."""
        mock_backend = Mock()
        mock_backend.handle_input = AsyncMock()
        
        input_sequence = ["/send", EOFError]  # Just /send with no content
        
        with patch('builtins.input', side_effect=input_sequence):
            await run_headless(backend=mock_backend, verbose=False)
            
            # Should not call backend for empty input
            mock_backend.handle_input.assert_not_called()

    @pytest.mark.asyncio
    async def test_whitespace_only_input_skipped(self):
        """Test that whitespace-only input is skipped."""
        mock_backend = Mock()
        mock_backend.handle_input = AsyncMock()
        
        input_sequence = ["   \n\t  ", "/send", EOFError]
        
        with patch('builtins.input', side_effect=input_sequence):
            await run_headless(backend=mock_backend, verbose=False)
            
            # Whitespace-only input should not call backend
            mock_backend.handle_input.assert_not_called()

    @pytest.mark.asyncio
    async def test_input_exception_handling(self):
        """Test handling input reading exceptions."""
        mock_backend = Mock()
        mock_backend.handle_input = AsyncMock()
        
        with patch('builtins.input', side_effect=Exception("Input error")):
            # Should not raise exception, should handle gracefully
            await run_headless(backend=mock_backend, verbose=False)
            
            mock_backend.handle_input.assert_not_called()

    @pytest.mark.asyncio
    async def test_backend_exception_handling(self):
        """Test handling backend exceptions."""
        mock_backend = Mock()
        mock_backend.handle_input = AsyncMock(side_effect=Exception("Backend error"))
        
        input_sequence = ["Test message", "/send", EOFError]
        
        with patch('builtins.input', side_effect=input_sequence):
            # Backend exception should propagate, not be caught silently
            with pytest.raises(Exception, match="Backend error"):
                await run_headless(backend=mock_backend, verbose=False)
            
            mock_backend.handle_input.assert_called_once_with("Test message")


class TestHeadlessModeIntegration:
    """Integration tests for headless mode."""

    @pytest.mark.asyncio
    async def test_realistic_conversation(self):
        """Test a realistic multi-turn conversation."""
        mock_backend = Mock()
        mock_backend.handle_input = AsyncMock()
        
        input_sequence = [
            "Hello, I need help with Python",
            "/send",
            "Can you explain list comprehensions?",
            "I want to understand the syntax",
            "/send", 
            "Thank you for the explanation",
            "/send",
            EOFError
        ]
        
        with patch('builtins.input', side_effect=input_sequence):
            await run_headless(backend=mock_backend, verbose=False)
            
            assert mock_backend.handle_input.call_count == 3
            expected_calls = [
                call("Hello, I need help with Python"),
                call("Can you explain list comprehensions?I want to understand the syntax"),
                call("Thank you for the explanation")
            ]
            mock_backend.handle_input.assert_has_calls(expected_calls)

    @pytest.mark.asyncio
    async def test_piped_input_simulation(self):
        """Test pattern typical of piped input."""
        mock_backend = Mock()
        mock_backend.handle_input = AsyncMock()
        
        # Simulate piped input that ends with EOF
        with patch('builtins.input', side_effect=["Analyze this data", EOFError]):
            await run_headless(backend=mock_backend, verbose=False)
            
            # Should process buffered content on EOF
            mock_backend.handle_input.assert_called_once_with("Analyze this data")

    @pytest.mark.asyncio
    async def test_mixed_content_and_send_commands(self):
        """Test mixing regular content with /send-like strings."""
        mock_backend = Mock()
        mock_backend.handle_input = AsyncMock()
        
        input_sequence = [
            "This message contains /send in the middle",
            "/send as a proper command",
            "/send",  # Actual send command
            EOFError
        ]
        
        with patch('builtins.input', side_effect=input_sequence):
            await run_headless(backend=mock_backend, verbose=False)
            
            expected_message = "This message contains /send in the middle/send as a proper command"
            mock_backend.handle_input.assert_called_once_with(expected_message)

    @pytest.mark.asyncio 
    async def test_send_command_with_whitespace(self):
        """Test /send command with surrounding whitespace."""
        mock_backend = Mock()
        mock_backend.handle_input = AsyncMock()
        
        input_sequence = ["test message", "  /send  ", EOFError]
        
        with patch('builtins.input', side_effect=input_sequence):
            await run_headless(backend=mock_backend, verbose=False)
            
            # Should still recognize /send with whitespace
            mock_backend.handle_input.assert_called_once_with("test message")

    @pytest.mark.asyncio
    async def test_function_return_value(self):
        """Test that function completes successfully."""
        mock_backend = Mock()
        mock_backend.handle_input = AsyncMock()
        
        with patch('builtins.input', side_effect=EOFError):
            # Should complete without raising exceptions
            result = await run_headless(backend=mock_backend, verbose=False)
            
            # Function should complete (return value not specified in original function)
            # Just testing that it doesn't crash