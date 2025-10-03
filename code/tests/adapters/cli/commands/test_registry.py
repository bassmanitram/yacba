"""
Tests for adapters.cli.commands.registry module.

Tests for the backend command registry with engine integration.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from adapters.cli.commands.registry import (
    BackendCommandRegistry, 
    COMMAND_REGISTRY
)
from adapters.cli.commands.adapted_commands import AdaptedCommands
from cli.commands.base_command import BaseCommand, CommandError


class TestBackendCommandRegistryData:
    """Test the COMMAND_REGISTRY data structure."""

    def test_registry_structure(self):
        """Test that COMMAND_REGISTRY has expected structure."""
        assert isinstance(COMMAND_REGISTRY, dict)
        assert len(COMMAND_REGISTRY) > 0

    def test_session_commands_registration(self):
        """Test that session commands are properly registered."""
        session_commands = ['/session', '/clear']
        
        for cmd in session_commands:
            assert cmd in COMMAND_REGISTRY
            cmd_info = COMMAND_REGISTRY[cmd]
            assert cmd_info['handler'] == 'adapters.cli.commands.session_commands.SessionCommands'
            assert cmd_info['category'] == 'Session Management'

    def test_info_commands_registration(self):
        """Test that info commands are properly registered."""
        info_commands = ['/history', '/tools', '/conversation-manager', '/conversation-stats']
        
        for cmd in info_commands:
            assert cmd in COMMAND_REGISTRY
            cmd_info = COMMAND_REGISTRY[cmd]
            assert cmd_info['handler'] == 'adapters.cli.commands.info_commands.InfoCommands'
            assert cmd_info['category'] == 'Information'

    def test_registry_entries_completeness(self):
        """Test that all registry entries have required fields."""
        required_fields = ['handler', 'category', 'description', 'usage']
        
        for command, info in COMMAND_REGISTRY.items():
            for field in required_fields:
                assert field in info, f"Command {command} missing field {field}"
            
            assert isinstance(info['usage'], list), f"Command {command} usage should be list"
            assert len(info['usage']) > 0, f"Command {command} should have at least one usage example"


class TestBackendCommandRegistryInit:
    """Test BackendCommandRegistry initialization."""

    def test_registry_initialization(self):
        """Test registry initialization with engine."""
        mock_engine = Mock()
        registry = BackendCommandRegistry(mock_engine)
        
        assert hasattr(registry, 'commands')
        assert hasattr(registry, 'command_cache')
        assert hasattr(registry, 'engine')
        assert registry.engine is mock_engine
        
        # Should have both base commands and backend commands
        assert '/help' in registry.commands  # From base registry
        assert '/session' in registry.commands  # From backend registry
        assert '/history' in registry.commands  # From backend registry


class TestBackendCommandRegistryHandlerInstantiation:
    """Test backend command handler instantiation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_engine = Mock()
        self.registry = BackendCommandRegistry(self.mock_engine)

    def test_instantiate_handler_none_class(self):
        """Test instantiating handler with None class."""
        result = self.registry._instantiate_handler('/test', None)
        assert result is None

    def test_instantiate_adapted_command_handler_simple(self):
        """Test instantiating adapted command handler with simple mock."""
        # Create a simple callable mock that returns a mock instance
        mock_handler_class = Mock()
        mock_instance = Mock()
        mock_handler_class.return_value = mock_instance
        
        with patch('builtins.issubclass', return_value=True):
            result = self.registry._instantiate_handler('/test', mock_handler_class)
            
            # Should call with registry and engine
            mock_handler_class.assert_called_once_with(self.registry, self.mock_engine)
            assert result is mock_instance


class TestBackendCommandRegistryHandlerRetrieval:
    """Test backend command handler retrieval."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_engine = Mock()
        self.registry = BackendCommandRegistry(self.mock_engine)

    def test_get_session_command_handler(self):
        """Test getting handler for session command."""
        with patch.object(self.registry, '_create_handler') as mock_create:
            mock_handler = Mock()
            mock_create.return_value = mock_handler
            
            result = self.registry.get_command_handler('/session')
            
            assert result is mock_handler
            mock_create.assert_called_once_with('adapters.cli.commands.session_commands.SessionCommands')

    def test_get_info_command_handler(self):
        """Test getting handler for info command."""
        with patch.object(self.registry, '_create_handler') as mock_create:
            mock_handler = Mock()
            mock_create.return_value = mock_handler
            
            result = self.registry.get_command_handler('/history')
            
            assert result is mock_handler
            mock_create.assert_called_once_with('adapters.cli.commands.info_commands.InfoCommands')

    def test_get_base_command_handler(self):
        """Test getting handler for base command (help)."""
        with patch.object(self.registry, '_create_handler') as mock_create:
            mock_handler = Mock()
            mock_create.return_value = mock_handler
            
            result = self.registry.get_command_handler('/help')
            
            assert result is mock_handler
            mock_create.assert_called_once_with('cli.commands.help_command.HelpCommand')

    def test_get_command_handler_caching_adapted(self):
        """Test that adapted handlers are cached properly."""
        with patch.object(self.registry, '_create_handler') as mock_create:
            mock_handler = Mock()
            mock_create.return_value = mock_handler
            
            # First call should create handler
            result1 = self.registry.get_command_handler('/session')
            assert result1 is mock_handler
            assert mock_create.call_count == 1
            
            # Cache should be populated
            handler_class = 'adapters.cli.commands.session_commands.SessionCommands'
            assert handler_class in self.registry.command_cache
            
            # Second call should use cache
            result2 = self.registry.get_command_handler('/session')
            assert result2 is mock_handler
            assert mock_create.call_count == 1  # Should not be called again


class TestBackendCommandRegistryHandling:
    """Test backend command handling functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_engine = Mock()
        self.registry = BackendCommandRegistry(self.mock_engine)

    @pytest.mark.asyncio
    async def test_handle_session_command(self):
        """Test handling session command."""
        mock_handler = Mock()
        mock_handler.handle_command = Mock()
        
        with patch.object(self.registry, 'get_command_handler', return_value=mock_handler):
            await self.registry.handle_command('/session test-session')
            
            mock_handler.handle_command.assert_called_once_with('/session', ['test-session'])

    @pytest.mark.asyncio
    async def test_handle_info_command(self):
        """Test handling info command."""
        mock_handler = Mock()
        mock_handler.handle_command = Mock()
        
        with patch.object(self.registry, 'get_command_handler', return_value=mock_handler):
            await self.registry.handle_command('/history')
            
            mock_handler.handle_command.assert_called_once_with('/history', [])

    @pytest.mark.asyncio
    async def test_handle_clear_command(self):
        """Test handling clear command."""
        mock_handler = Mock()
        mock_handler.handle_command = Mock()
        
        with patch.object(self.registry, 'get_command_handler', return_value=mock_handler):
            await self.registry.handle_command('/clear')
            
            mock_handler.handle_command.assert_called_once_with('/clear', [])

    @pytest.mark.asyncio
    async def test_handle_command_with_args(self):
        """Test handling command with multiple arguments."""
        mock_handler = Mock()
        mock_handler.handle_command = Mock()
        
        with patch.object(self.registry, 'get_command_handler', return_value=mock_handler):
            await self.registry.handle_command('/session arg1 arg2 arg3')
            
            mock_handler.handle_command.assert_called_once_with('/session', ['arg1', 'arg2', 'arg3'])


class TestBackendCommandRegistryValidation:
    """Test backend command validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_engine = Mock()
        self.registry = BackendCommandRegistry(self.mock_engine)

    def test_validate_backend_commands(self):
        """Test validation of backend-specific commands."""
        backend_commands = ['/session', '/clear', '/history', '/tools', '/conversation-manager', '/conversation-stats']
        
        for cmd in backend_commands:
            assert self.registry.validate_command(cmd) is True

    def test_validate_base_commands(self):
        """Test validation of base commands."""
        base_commands = ['/help', '/exit', '/quit']
        
        for cmd in base_commands:
            assert self.registry.validate_command(cmd) is True

    def test_validate_invalid_commands(self):
        """Test validation of invalid commands."""
        invalid_commands = ['/invalid', '/nonexistent', '/fake']
        
        for cmd in invalid_commands:
            assert self.registry.validate_command(cmd) is False


class TestBackendCommandRegistryHelp:
    """Test backend command help functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_engine = Mock()
        self.registry = BackendCommandRegistry(self.mock_engine)

    def test_get_command_help_session(self):
        """Test getting help for session command."""
        help_text = self.registry.get_command_help('/session')
        
        assert isinstance(help_text, str)
        assert '/session' in help_text
        assert 'Manage conversation sessions' in help_text

    def test_get_command_help_clear(self):
        """Test getting help for clear command."""
        help_text = self.registry.get_command_help('/clear')
        
        assert isinstance(help_text, str)
        assert '/clear' in help_text
        assert 'Clear current conversation' in help_text

    def test_get_command_help_history(self):
        """Test getting help for history command."""
        help_text = self.registry.get_command_help('/history')
        
        assert isinstance(help_text, str)
        assert '/history' in help_text
        assert 'Show conversation history' in help_text

    def test_get_command_help_all_commands(self):
        """Test getting help for all commands includes backend commands."""
        help_text = self.registry.get_command_help()
        
        assert isinstance(help_text, str)
        assert 'Available commands:' in help_text
        
        # Should include backend commands
        assert '/session' in help_text
        assert '/clear' in help_text
        assert '/history' in help_text
        assert '/tools' in help_text
        
        # Should also include base commands
        assert '/help' in help_text
        assert '/exit' in help_text


class TestBackendCommandRegistryIntegration:
    """Integration tests for BackendCommandRegistry."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_engine = Mock()
        self.registry = BackendCommandRegistry(self.mock_engine)

    def test_full_backend_command_workflow(self):
        """Test complete backend command workflow."""
        # 1. Validate command exists
        assert self.registry.validate_command('/session') is True
        
        # 2. Get help text
        help_text = self.registry.get_command_help('/session')
        assert isinstance(help_text, str)
        assert len(help_text) > 0
        
        # 3. List all commands includes backend commands
        commands = self.registry.list_commands()
        assert '/session' in commands
        assert '/history' in commands
        assert '/clear' in commands

    @pytest.mark.asyncio
    async def test_end_to_end_backend_command_handling(self):
        """Test end-to-end backend command handling."""
        # Create a mock adapted handler
        mock_handler = Mock()
        mock_handler.handle_command = Mock()
        
        with patch.object(self.registry, '_create_handler', return_value=mock_handler):
            # Handle session command with arguments
            await self.registry.handle_command('/session test-session')
            
            # Verify adapted handler was called correctly with engine
            mock_handler.handle_command.assert_called_once_with('/session', ['test-session'])
            
            # Verify caching works for adapted commands
            await self.registry.handle_command('/session another-session')
            assert mock_handler.handle_command.call_count == 2

    def test_mixed_command_types_workflow(self):
        """Test workflow with both base and backend commands."""
        # Backend commands
        backend_commands = ['/session', '/clear', '/history']
        for cmd in backend_commands:
            assert self.registry.validate_command(cmd) is True
        
        # Base commands
        base_commands = ['/help', '/exit']
        for cmd in base_commands:
            assert self.registry.validate_command(cmd) is True
        
        # All should be listed
        all_commands = self.registry.list_commands()
        for cmd in backend_commands + base_commands:
            assert cmd in all_commands

    def test_engine_integration_simple(self):
        """Test that engine is properly integrated."""
        # Registry should have engine
        assert self.registry.engine is self.mock_engine
        
        # When creating adapted handlers, engine should be passed
        with patch.object(self.registry, '_load_handler') as mock_load:
            mock_class = Mock()
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            mock_load.return_value = mock_class
            
            with patch('builtins.issubclass', return_value=True):
                handler = self.registry._create_handler('adapters.cli.commands.session_commands.SessionCommands')
                
                # Should have been called with registry and engine
                mock_class.assert_called_once_with(self.registry, self.mock_engine)
                assert handler is mock_instance