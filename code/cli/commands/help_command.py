"""
Help command for YACBA CLI.

Provides comprehensive help information for all available commands.
This is separate from other info commands because it needs to know
about commands across all command modules.
"""

from typing import List, Dict, Any

from .registry import COMMAND_REGISTRY
from .base_command import BaseCommand


class HelpCommand(BaseCommand):
    """Handler for the /help command."""
    
    async def handle_command(self, command: str, args: List[str]) -> None:
        """
        Handle the /help command.
        
        Args:
            command: Should be "/help"
            args: Optional specific command to get help for
        """
        if command != "/help":
            self.print_error(f"HelpCommand can only handle /help, got: {command}")
            return
        
        await self._show_help(args)
    
    async def _show_help(self, args: List[str]) -> None:
        """
        Show help information for commands.
        
        Args:
            args: Optional specific command to get help for
        """
        if not self.validate_args(args, max_args=1):
            return
        
        if args:
            # Help for specific command
            command = args[0]
            if not command.startswith('/'):
                command = f'/{command}'
            
            if self.registry.validate_command(command):
                help_text = self.registry.get_command_help(command)
                self.print_info(help_text)
            else:
                self.print_error(f"Unknown command: {command}")
                self.print_info("\nAvailable commands:")
                self._show_command_summary()
        else:
            # General help
            self._show_general_help()
    
    def _show_general_help(self) -> None:
        """Show general help with all available commands."""
        self.print_info("Welcome to YACBA (Yet Another ChatBot Agent)!")
        self.print_info("")
        self.print_info("Available meta-commands:")
        
        # Group commands by category for better organization
        command_categories = self._group_commands_by_category()
        
        for category, commands in command_categories.items():
            self.print_info(f"\n{category}:")
            for cmd, info in commands.items():
                # Show primary usage for each command
                primary_usage = info['usage'][0] if info['usage'] else cmd
                self.print_info(f"  {primary_usage:<25} - {info['description']}")
        
        self.print_info("")
        self.print_info("Usage tips:")
        self.print_info("  • Use '/help <command>' for detailed information about a specific command")
        self.print_info("  • Use Enter to add new lines while typing")
        self.print_info("  • Use Alt+Enter or Ctrl+J to send your message")
        self.print_info("  • Use file('path/to/file') to upload files during conversation")
        self.print_info("  • Use Ctrl+D or Ctrl+C to exit")
    
    def _group_commands_by_category(self) -> Dict[str, Dict[str, Any]]:
        """
        Group commands by logical categories for better help display.
        
        Returns:
            Dictionary of categories with their commands
        """
        categories = {}
        
        
        for cmd, info in COMMAND_REGISTRY.items():
            category = info.get('category', 'General')
            if category not in categories:
                categories[category] = {}
            categories[category][cmd] = info
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def get_command_usage(self, command: str) -> str:
        """
        Get usage information for the help command.
        
        Args:
            command: Should be "/help"
            
        Returns:
            Usage string
        """
        if command == "/help":
            return "/help [command] - Show help for all commands or detailed help for a specific command"
        return super().get_command_usage(command)