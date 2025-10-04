"""
Integration tests for YACBA repl_toolkit adapters.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from adapters.repl import YacbaAsyncBackend, BackendCommandRegistry, YacbaCompleter


class TestAdapterIntegration:
    """Test integration between adapters."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock engine
        self.mock_engine = Mock()
        self.mock_engine.handle_input = AsyncMock()
        
        # Create adapters
        self.backend = YacbaAsyncBackend(self.mock_engine)
        self.command_registry = BackendCommandRegistry(self.mock_engine)
        self.completer = YacbaCompleter(["/help", "/session", "/history"])

    @pytest.mark.asyncio
    async def test_full_repl_workflow_simulation(self):
        """Test simulated full REPL workflow with all adapters."""
        # Simulate user input processing
        user_input = "Hello, how are you?"
        
        # Test backend handles input
        result = await self.backend.handle_input(user_input)
        assert result is True
        self.mock_engine.handle_input.assert_called_once_with(user_input)
        
        # Test command handling
        command = "/help"
        await self.command_registry.handle_command(command)
        # Command registry should handle the command (no exception raised)
        
        # Test completion
        mock_document = Mock()
        mock_document.text_before_cursor = "/h"
        mock_event = Mock()
        
        completions = list(self.completer.get_completions(mock_document, mock_event))
        # Should get completions for commands starting with /h
        completion_texts = [c.text for c in completions]
        assert "/help" in completion_texts or "/history" in completion_texts

    def test_adapter_protocol_compliance(self):
        """Test that all adapters implement the expected protocols."""
        # Import protocols
        from repl_toolkit import AsyncBackend, CommandHandler, Completer
        
        # Test protocol compliance
        assert isinstance(self.backend, AsyncBackend)
        assert isinstance(self.command_registry, CommandHandler) 
        assert isinstance(self.completer, Completer)

    @pytest.mark.asyncio
    async def test_error_handling_across_adapters(self):
        """Test error handling across all adapters."""
        # Test backend error handling
        self.mock_engine.handle_input.side_effect = Exception("Engine error")
        result = await self.backend.handle_input("test")
        assert result is False
        
        # Test command handler error handling (should not raise)
        # Using a non-existent command should be handled gracefully
        await self.command_registry.handle_command("/nonexistent")  # Should not raise
        
        # Reset for next test
        self.mock_engine.handle_input.side_effect = None