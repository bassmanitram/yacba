"""
Tests for cli.commands.help_command module.

Comprehensive testing of the help command system and dynamic help generation.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from cli.commands.help_command import HelpCommand
from cli.commands.registry import COMMAND_REGISTRY


class TestHelpCommandInit:
    """Test HelpCommand initialization."""

    def test_help_command_initialization(self):
        """Test HelpCommand initialization."""
        mock_registry = Mock()
        help_cmd = HelpCommand(mock_registry)
        
        assert help_cmd.registry is mock_registry
        assert help_cmd._command_name == "helpcommand"


class TestHelpCommandValidation:
    """Test help command validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = Mock()
        self.help_cmd = HelpCommand(self.mock_registry)

    @pytest.mark.asyncio
    async def test_handle_command_valid_help(self):
        """Test handling valid /help command."""
        with patch.object(self.help_cmd, '_show_help') as mock_show_help:
            await self.help_cmd.handle_command('/help', [])
            mock_show_help.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_handle_command_valid_help_with_args(self):
        """Test handling /help command with arguments."""
        with patch.object(self.help_cmd, '_show_help') as mock_show_help:
            await self.help_cmd.handle_command('/help', ['command'])
            mock_show_help.assert_called_once_with(['command'])

    @pytest.mark.asyncio
    async def test_handle_command_invalid_command(self):
        """Test handling invalid command."""
        with patch.object(self.help_cmd, 'print_error') as mock_print_error:
            await self.help_cmd.handle_command('/invalid', [])
            
            mock_print_error.assert_called_once()
            call_args = mock_print_error.call_args[0][0]
            assert 'HelpCommand can only handle /help' in call_args
            assert '/invalid' in call_args


class TestShowHelpFunctionality:
    """Test the _show_help method functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = Mock()
        self.help_cmd = HelpCommand(self.mock_registry)

    @pytest.mark.asyncio
    async def test_show_help_no_args(self):
        """Test showing general help with no arguments."""
        with patch.object(self.help_cmd, '_show_general_help') as mock_general:
            await self.help_cmd._show_help([])
            mock_general.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_help_specific_command_valid(self):
        """Test showing help for specific valid command."""
        self.mock_registry.validate_command.return_value = True
        self.mock_registry.get_command_help.return_value = "Help for /test command"
        
        with patch.object(self.help_cmd, 'print_info') as mock_print_info:
            await self.help_cmd._show_help(['test'])
            
            self.mock_registry.validate_command.assert_called_once_with('/test')
            self.mock_registry.get_command_help.assert_called_once_with('/test')
            mock_print_info.assert_called_once_with("Help for /test command")

    @pytest.mark.asyncio
    async def test_show_help_specific_command_with_slash(self):
        """Test showing help for command already with slash prefix."""
        self.mock_registry.validate_command.return_value = True
        self.mock_registry.get_command_help.return_value = "Help for /test command"
        
        with patch.object(self.help_cmd, 'print_info') as mock_print_info:
            await self.help_cmd._show_help(['/test'])
            
            self.mock_registry.validate_command.assert_called_once_with('/test')

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_show_help_specific_command_invalid(self):
        """Test showing help for invalid command."""
        self.mock_registry.validate_command.return_value = False
        
        with patch.object(self.help_cmd, "print_error") as mock_print_error:
            with patch.object(self.help_cmd, "print_info") as mock_print_info:
                with patch.object(self.help_cmd, "_show_command_summary", create=True) as mock_summary:
                    await self.help_cmd._show_help(["invalid"])
                    
                    mock_print_error.assert_called_once_with("Unknown command: /invalid")
                    mock_print_info.assert_called_once_with("\nAvailable commands:")
                    mock_summary.assert_called_once()


    @pytest.mark.asyncio
    async def test_show_help_too_many_args(self):
        """Test showing help with too many arguments."""
        with patch.object(self.help_cmd, 'validate_args', return_value=False) as mock_validate:
            await self.help_cmd._show_help(['arg1', 'arg2'])
            
            mock_validate.assert_called_once_with(['arg1', 'arg2'], max_args=1)


class TestGeneralHelpDisplay:
    """Test general help display functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = Mock()
        self.help_cmd = HelpCommand(self.mock_registry)

    def test_show_general_help_structure(self):
        """Test general help display structure."""
        with patch.object(self.help_cmd, 'print_info') as mock_print_info:
            with patch.object(self.help_cmd, '_group_commands_by_category') as mock_group:
                mock_group.return_value = {
                    'General': {
                        '/help': {
                            'description': 'Show help information',
                            'usage': ['/help - Show all commands']
                        }
                    },
                    'Control': {
                        '/exit': {
                            'description': 'Exit the application',
                            'usage': ['/exit - Exit YACBA']
                        }
                    }
                }
                
                self.help_cmd._show_general_help()
                
                # Check that welcome message was printed
                print_calls = [call[0][0] for call in mock_print_info.call_args_list]
                assert any("Welcome to YACBA" in call for call in print_calls)
                assert any("Available meta-commands:" in call for call in print_calls)
                assert any("General:" in call for call in print_calls)
                assert any("Control:" in call for call in print_calls)
                assert any("Usage tips:" in call for call in print_calls)

    def test_group_commands_by_category(self):
        """Test command grouping by category."""
        # Use real COMMAND_REGISTRY for this test
        result = self.help_cmd._group_commands_by_category()
        
        assert isinstance(result, dict)
        assert len(result) > 0
        
        # Should have at least General and Control categories
        assert 'General' in result
        assert 'Control' in result
        
        # General should contain help command
        assert '/help' in result['General']
        
        # Control should contain exit/quit commands
        control_commands = list(result['Control'].keys())
        assert '/exit' in control_commands
        assert '/quit' in control_commands

    def test_group_commands_structure(self):
        """Test that grouped commands have proper structure."""
        result = self.help_cmd._group_commands_by_category()
        
        for category, commands in result.items():
            assert isinstance(category, str)
            assert isinstance(commands, dict)
            
            for command, info in commands.items():
                assert command.startswith('/')
                assert 'description' in info
                assert 'usage' in info
                assert isinstance(info['usage'], list)


class TestCommandUsage:
    """Test command usage functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = Mock()
        self.help_cmd = HelpCommand(self.mock_registry)

    def test_get_command_usage_help(self):
        """Test usage string for help command."""
        result = self.help_cmd.get_command_usage('/help')
        
        assert isinstance(result, str)
        assert '/help' in result
        assert 'Show help for all commands' in result
        assert 'detailed help for a specific command' in result

    def test_get_command_usage_other(self):
        """Test usage string for non-help command."""
        result = self.help_cmd.get_command_usage('/other')
        
        assert isinstance(result, str)
        assert 'Usage: /other [args...]' in result


class TestHelpCommandIntegration:
    """Integration tests for HelpCommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = Mock()
        self.help_cmd = HelpCommand(self.mock_registry)

    @pytest.mark.asyncio
    async def test_full_help_workflow_general(self):
        """Test complete workflow for general help."""
        with patch.object(self.help_cmd, 'print_info') as mock_print_info:
            with patch.object(self.help_cmd, '_group_commands_by_category') as mock_group:
                mock_group.return_value = {
                    'General': {
                        '/help': {
                            'description': 'Show help',
                            'usage': ['/help']
                        }
                    }
                }
                
                await self.help_cmd.handle_command('/help', [])
                
                # Should have printed welcome and command info
                assert mock_print_info.call_count > 0

    @pytest.mark.asyncio
    async def test_full_help_workflow_specific(self):
        """Test complete workflow for specific command help."""
        self.mock_registry.validate_command.return_value = True
        self.mock_registry.get_command_help.return_value = "Detailed help text"
        
        with patch.object(self.help_cmd, 'print_info') as mock_print_info:
            await self.help_cmd.handle_command('/help', ['test'])
            
            self.mock_registry.validate_command.assert_called_once_with('/test')
            self.mock_registry.get_command_help.assert_called_once_with('/test')
            mock_print_info.assert_called_once_with("Detailed help text")

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Test error handling in help command."""
        # Test invalid command name
        await self.help_cmd.handle_command('/invalid', [])
        
        # Test too many arguments
        with patch.object(self.help_cmd, 'validate_args', return_value=False):
            await self.help_cmd._show_help(['arg1', 'arg2'])

    def test_real_command_registry_integration(self):
        """Test integration with real command registry."""
        # Test with actual COMMAND_REGISTRY
        categories = self.help_cmd._group_commands_by_category()
        
        # Should process real registry entries
        assert len(categories) > 0
        
        # Should have proper structure
        for category, commands in categories.items():
            for command, info in commands.items():
                # Verify structure matches COMMAND_REGISTRY
                assert command in COMMAND_REGISTRY
                registry_info = COMMAND_REGISTRY[command]
                assert info['description'] == registry_info['description']
                assert info['usage'] == registry_info['usage']


class TestHelpCommandErrorCases:
    """Test error cases and edge conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = Mock()
        self.help_cmd = HelpCommand(self.mock_registry)

    @pytest.mark.asyncio
    async def test_show_help_empty_registry(self):
        """Test help display with empty command registry."""
        with patch('cli.commands.help_command.COMMAND_REGISTRY', {}):
            categories = self.help_cmd._group_commands_by_category()
            assert categories == {}

    @pytest.mark.asyncio 
    async def test_show_help_malformed_registry(self):
        """Test help with malformed registry entries."""
        malformed_registry = {
            '/test': {
                'description': 'Test command',
                # Missing other required fields
            }
        }
        
        with patch('cli.commands.help_command.COMMAND_REGISTRY', malformed_registry):
            # Should handle missing fields gracefully
            categories = self.help_cmd._group_commands_by_category()
            assert '/test' in categories.get('General', {})

    def test_format_with_empty_usage(self):
        """Test formatting commands with empty usage lists."""
        with patch('cli.commands.help_command.COMMAND_REGISTRY', {
            '/test': {
                'handler': 'test.Handler',
                'category': 'Test',
                'description': 'Test command',
                'usage': []  # Empty usage
            }
        }):
            categories = self.help_cmd._group_commands_by_category()
            test_info = categories['Test']['/test']
            assert test_info['usage'] == []