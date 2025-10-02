"""
Tests for cli.commands.registry module.

Comprehensive testing of command registry, validation, and dynamic loading.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from cli.commands.registry import (
    CommandRegistry, 
    COMMAND_REGISTRY
)
from cli.commands.base_command import BaseCommand, CommandError


class MockCommand(BaseCommand):
    """Mock command for testing."""
    
    def __init__(self, registry):
        self.registry = registry
        self._command_name = "mockcommand"
        self.handle_called = False
        self.last_command = None
        self.last_args = None

    async def handle_command(self, command: str, args: list) -> None:
        self.handle_called = True
        self.last_command = command
        self.last_args = args


class TestCommandRegistryData:
    """Test the COMMAND_REGISTRY data structure."""

    def test_registry_structure(self):
        """Test that COMMAND_REGISTRY has expected structure."""
        assert isinstance(COMMAND_REGISTRY, dict)
        assert len(COMMAND_REGISTRY) > 0

    def test_help_command_registration(self):
        """Test that help command is properly registered."""
        assert '/help' in COMMAND_REGISTRY
        help_info = COMMAND_REGISTRY['/help']
        
        assert 'handler' in help_info
        assert 'category' in help_info
        assert 'description' in help_info
        assert 'usage' in help_info
        
        assert help_info['handler'] == 'cli.commands.help_command.HelpCommand'
        assert help_info['category'] == 'General'
        assert isinstance(help_info['usage'], list)

    def test_control_commands_registration(self):
        """Test that control commands are registered."""
        control_commands = ['/exit', '/quit']
        
        for cmd in control_commands:
            assert cmd in COMMAND_REGISTRY
            cmd_info = COMMAND_REGISTRY[cmd]
            assert cmd_info['handler'] == 'MainLoop'
            assert cmd_info['category'] == 'Control'

    def test_registry_entries_completeness(self):
        """Test that all registry entries have required fields."""
        required_fields = ['handler', 'category', 'description', 'usage']
        
        for command, info in COMMAND_REGISTRY.items():
            for field in required_fields:
                assert field in info, f"Command {command} missing field {field}"
            
            assert isinstance(info['usage'], list), f"Command {command} usage should be list"
            assert len(info['usage']) > 0, f"Command {command} should have at least one usage example"


class TestCommandRegistryInit:
    """Test CommandRegistry initialization."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = CommandRegistry()
        
        assert hasattr(registry, 'commands')
        assert hasattr(registry, 'command_cache')
        assert registry.commands is COMMAND_REGISTRY
        assert isinstance(registry.command_cache, dict)
        assert len(registry.command_cache) == 0  # Should start empty


class TestCommandValidation:
    """Test command validation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = CommandRegistry()

    def test_validate_command_existing(self):
        """Test validation of existing commands."""
        assert self.registry.validate_command('/help') is True
        assert self.registry.validate_command('/exit') is True
        assert self.registry.validate_command('/quit') is True

    def test_validate_command_nonexistent(self):
        """Test validation of non-existent commands."""
        assert self.registry.validate_command('/nonexistent') is False
        assert self.registry.validate_command('/fake') is False
        assert self.registry.validate_command('/invalid') is False

    def test_validate_command_edge_cases(self):
        """Test validation edge cases."""
        assert self.registry.validate_command('') is False
        assert self.registry.validate_command('help') is False  # No leading slash
        assert self.registry.validate_command('//help') is False
        assert self.registry.validate_command('/HELP') is False  # Case sensitive


class TestCommandListing:
    """Test command listing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = CommandRegistry()

    def test_list_commands(self):
        """Test listing all commands."""
        commands = self.registry.list_commands()
        
        assert isinstance(commands, list)
        assert len(commands) > 0
        assert '/help' in commands
        assert '/exit' in commands
        assert '/quit' in commands
        
        # Should be sorted
        assert commands == sorted(commands)

    def test_list_commands_contains_all_registry_commands(self):
        """Test that list_commands returns all registry commands."""
        commands = self.registry.list_commands()
        registry_commands = list(COMMAND_REGISTRY.keys())
        
        assert len(commands) == len(registry_commands)
        for cmd in registry_commands:
            assert cmd in commands


class TestCommandHelp:
    """Test command help functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = CommandRegistry()

    def test_get_command_help_specific(self):
        """Test getting help for specific command."""
        help_text = self.registry.get_command_help('/help')
        
        assert isinstance(help_text, str)
        assert '/help' in help_text
        assert 'Show help information' in help_text
        assert 'Usage:' in help_text or '/help' in help_text

    def test_get_command_help_nonexistent(self):
        """Test getting help for non-existent command."""
        help_text = self.registry.get_command_help('/nonexistent')
        
        # Should return general help for non-existent commands
        assert "Available commands:" in help_text

    def test_get_command_help_all_commands(self):
        """Test getting help for all commands."""
        help_text = self.registry.get_command_help()
        
        assert isinstance(help_text, str)
        assert 'Available commands:' in help_text
        assert '/help' in help_text
        assert '/exit' in help_text

    def test_get_command_help_none_parameter(self):
        """Test getting help with None parameter."""
        help_text = self.registry.get_command_help(None)
        
        assert isinstance(help_text, str)
        assert 'Available commands:' in help_text


class TestCommandHandlerLoading:
    """Test dynamic command handler loading."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = CommandRegistry()

    def test_load_handler_valid_path(self):
        """Test loading valid handler class."""
        # Mock the import process
        with patch('builtins.__import__') as mock_import:
            mock_module = Mock()
            mock_class = Mock()
            mock_module.HelpCommand = mock_class
            mock_import.return_value = mock_module
            
            result = self.registry._load_handler('cli.commands.help_command.HelpCommand')
            
            assert result is mock_class
            mock_import.assert_called_once_with('cli.commands.help_command', fromlist=['HelpCommand'])

    def test_load_handler_invalid_path(self):
        """Test loading invalid handler path."""
        with pytest.raises((AttributeError, ModuleNotFoundError)):
            self.registry._load_handler('invalid.path.InvalidClass')

    def test_instantiate_handler(self):
        """Test handler instantiation."""
        mock_class = Mock()
        mock_instance = Mock()
        mock_class.return_value = mock_instance
        
        result = self.registry._instantiate_handler('TestHandler', mock_class)
        
        assert result is mock_instance
        mock_class.assert_called_once_with(self.registry)

    def test_create_handler_success(self):
        """Test successful handler creation."""
        with patch.object(self.registry, '_load_handler') as mock_load:
            with patch.object(self.registry, '_instantiate_handler') as mock_instantiate:
                mock_class = Mock()
                mock_class.__bases__ = (BaseCommand,)
                mock_load.return_value = mock_class
                mock_instance = Mock()
                mock_instantiate.return_value = mock_instance
                
                # Mock issubclass to return True
                with patch('builtins.issubclass', return_value=True):
                    result = self.registry._create_handler('test.Handler')
                
                assert result is mock_instance
                mock_load.assert_called_once_with('test.Handler')
                mock_instantiate.assert_called_once_with('test.Handler', mock_class)

    def test_create_handler_invalid_base_class(self):
        """Test handler creation with invalid base class."""
        with patch.object(self.registry, '_load_handler') as mock_load:
            mock_class = Mock()
            mock_load.return_value = mock_class
            
            # Mock issubclass to return False (invalid base class)
            with patch('builtins.issubclass', return_value=False):
                # The method should raise TypeError for invalid base class
                try:
                    self.registry._create_handler('test.InvalidHandler')
                    assert False, "Expected TypeError to be raised"
                except TypeError:
                    pass  # This is expected


class TestCommandHandlerRetrieval:
    """Test command handler retrieval and caching."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = CommandRegistry()

    def test_get_command_handler_help(self):
        """Test getting handler for help command."""
        with patch.object(self.registry, '_create_handler') as mock_create:
            mock_handler = Mock()
            mock_create.return_value = mock_handler
            
            result = self.registry.get_command_handler('/help')
            
            assert result is mock_handler
            mock_create.assert_called_once_with('cli.commands.help_command.HelpCommand')

    def test_get_command_handler_mainloop(self):
        """Test getting handler for MainLoop commands."""
        result = self.registry.get_command_handler('/exit')
        assert result is None
        
        result = self.registry.get_command_handler('/quit')
        assert result is None

    def test_get_command_handler_invalid(self):
        """Test getting handler for invalid command."""
        with pytest.raises(CommandError) as exc_info:
            self.registry.get_command_handler('/invalid')
        
        assert 'not recognized' in str(exc_info.value)
        assert exc_info.value.command == '/invalid'

    def test_get_command_handler_auto_slash(self):
        """Test handler retrieval with automatic slash prefix."""
        with patch.object(self.registry, '_create_handler') as mock_create:
            mock_handler = Mock()
            mock_create.return_value = mock_handler
            
            result = self.registry.get_command_handler('help')  # No leading slash
            
            assert result is mock_handler

    def test_get_command_handler_caching(self):
        """Test that handlers are cached properly."""
        with patch.object(self.registry, '_create_handler') as mock_create:
            mock_handler = Mock()
            mock_create.return_value = mock_handler
            
            # First call should create handler
            result1 = self.registry.get_command_handler('/help')
            assert result1 is mock_handler
            assert mock_create.call_count == 1
            
            # Cache should be populated
            assert 'cli.commands.help_command.HelpCommand' in self.registry.command_cache
            
            # Second call should use cache
            result2 = self.registry.get_command_handler('/help')
            assert result2 is mock_handler
            assert mock_create.call_count == 1  # Should not be called again


class TestCommandHandling:
    """Test command handling functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = CommandRegistry()

    @pytest.mark.asyncio
    async def test_handle_command_basic(self):
        """Test basic command handling."""
        mock_handler = Mock()
        mock_handler.handle_command = Mock()
        
        with patch.object(self.registry, 'get_command_handler', return_value=mock_handler):
            await self.registry.handle_command('/help arg1 arg2')
            
            mock_handler.handle_command.assert_called_once_with('/help', ['arg1', 'arg2'])

    @pytest.mark.asyncio
    async def test_handle_command_no_args(self):
        """Test command handling with no arguments."""
        mock_handler = Mock()
        mock_handler.handle_command = Mock()
        
        with patch.object(self.registry, 'get_command_handler', return_value=mock_handler):
            await self.registry.handle_command('/help')
            
            mock_handler.handle_command.assert_called_once_with('/help', [])

    @pytest.mark.asyncio
    async def test_handle_command_auto_slash(self):
        """Test command handling with automatic slash prefix."""
        mock_handler = Mock()
        mock_handler.handle_command = Mock()
        
        with patch.object(self.registry, 'get_command_handler', return_value=mock_handler):
            await self.registry.handle_command('help')  # No leading slash
            
            mock_handler.handle_command.assert_called_once_with('/help', [])

    @pytest.mark.asyncio
    async def test_handle_command_mainloop(self):
        """Test handling MainLoop commands."""
        # MainLoop commands return None handler and should not raise errors
        await self.registry.handle_command('/exit')
        await self.registry.handle_command('/quit')

    @pytest.mark.asyncio
    async def test_handle_command_invalid(self):
        """Test handling invalid commands."""
        with patch('builtins.print') as mock_print:
            with pytest.raises(CommandError):
                await self.registry.handle_command('/invalid')

    @pytest.mark.asyncio
    async def test_handle_command_exception(self):
        """Test command handling with handler exception."""
        mock_handler = Mock()
        mock_handler.handle_command.side_effect = Exception("Handler error")
        
        with patch.object(self.registry, 'get_command_handler', return_value=mock_handler):
            with patch('builtins.print') as mock_print:
                await self.registry.handle_command('/help')
                
                # Should print error message
                mock_print.assert_called()
                call_args = mock_print.call_args[0][0]
                assert 'Error handling command' in call_args
                assert 'Handler error' in call_args


class TestCommandRegistryManagement:
    """Test command registry management functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = CommandRegistry()

    def test_add_command_success(self):
        """Test successfully adding a new command."""
        self.registry.add_command(
            command='/test',
            handler='test.TestHandler',
            category='Test',
            description='Test command',
            usage=['/test - Test usage']
        )
        
        assert '/test' in self.registry.commands
        cmd_info = self.registry.commands['/test']
        assert cmd_info['handler'] == 'test.TestHandler'
        assert cmd_info['category'] == 'Test'
        assert cmd_info['description'] == 'Test command'
        assert cmd_info['usage'] == ['/test - Test usage']

    def test_add_command_duplicate(self):
        """Test adding duplicate command raises error."""
        with pytest.raises(ValueError) as exc_info:
            self.registry.add_command(
                command='/help',  # Already exists
                handler='test.Handler',
                category='Test',
                description='Test',
                usage=['test']
            )
        
        assert 'already exists' in str(exc_info.value)


class TestCommandRegistryIntegration:
    """Integration tests for CommandRegistry."""

    def setup_method(self):
        """Set up test fixtures.""" 
        self.registry = CommandRegistry()

    def test_full_command_workflow(self):
        """Test complete command workflow."""
        # 1. Validate command exists
        assert self.registry.validate_command('/help') is True
        
        # 2. Get help text
        help_text = self.registry.get_command_help('/help')
        assert isinstance(help_text, str)
        assert len(help_text) > 0
        
        # 3. List all commands
        commands = self.registry.list_commands()
        assert '/help' in commands

    @pytest.mark.asyncio
    async def test_end_to_end_command_handling(self):
        """Test end-to-end command handling with mocked handler."""
        # Create a complete mock handler
        mock_handler = Mock()
        mock_handler.handle_command = Mock()
        
        with patch.object(self.registry, '_create_handler', return_value=mock_handler):
            # Handle command with arguments
            await self.registry.handle_command('/help test arg')
            
            # Verify handler was called correctly
            mock_handler.handle_command.assert_called_once_with('/help', ['test', 'arg'])
            
            # Verify caching works
            await self.registry.handle_command('/help another arg')
            assert mock_handler.handle_command.call_count == 2