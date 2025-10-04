"""
Tests for YACBA repl_toolkit backend adapters.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from adapters.repl.backend_adapter import YacbaAsyncBackend, YacbaHeadlessBackend
from repl_toolkit.ptypes import AsyncBackend, HeadlessBackend


class TestYacbaAsyncBackend:
    """Test YacbaAsyncBackend adapter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_engine = Mock()
        self.mock_engine.handle_input = AsyncMock()
        self.backend = YacbaAsyncBackend(self.mock_engine)

    def test_implements_async_backend_protocol(self):
        """Test that YacbaAsyncBackend implements AsyncBackend protocol."""
        assert isinstance(self.backend, AsyncBackend)

    @pytest.mark.asyncio
    async def test_handle_input_success(self):
        """Test successful input handling."""
        user_input = "Test message"
        
        # Mock successful engine call
        self.mock_engine.handle_input.return_value = None
        
        result = await self.backend.handle_input(user_input)
        
        assert result is True
        self.mock_engine.handle_input.assert_called_once_with(user_input)

    @pytest.mark.asyncio
    async def test_handle_input_exception(self):
        """Test input handling with engine exception."""
        user_input = "Test message"
        
        # Mock engine exception
        self.mock_engine.handle_input.side_effect = Exception("Engine error")
        
        result = await self.backend.handle_input(user_input)
        
        assert result is False
        self.mock_engine.handle_input.assert_called_once_with(user_input)


class TestYacbaHeadlessBackend:
    """Test YacbaHeadlessBackend adapter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_engine = Mock()
        self.mock_engine.handle_input = AsyncMock()
        self.backend = YacbaHeadlessBackend(self.mock_engine)

    def test_implements_headless_backend_protocol(self):
        """Test that YacbaHeadlessBackend implements HeadlessBackend protocol."""
        assert isinstance(self.backend, HeadlessBackend)

    @pytest.mark.asyncio
    async def test_handle_input_success(self):
        """Test successful input handling."""
        user_input = "Test message"
        
        # Mock successful engine call
        self.mock_engine.handle_input.return_value = None
        
        result = await self.backend.handle_input(user_input)
        
        assert result is True
        self.mock_engine.handle_input.assert_called_once_with(user_input)

    @pytest.mark.asyncio
    async def test_handle_input_exception(self):
        """Test input handling with engine exception."""
        user_input = "Test message"
        
        # Mock engine exception
        self.mock_engine.handle_input.side_effect = Exception("Engine error")
        
        result = await self.backend.handle_input(user_input)
        
        assert result is False
        self.mock_engine.handle_input.assert_called_once_with(user_input)