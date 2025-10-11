"""Command registry for validation and help generation."""
from typing import Any
from loguru import logger

from repl_toolkit.commands.registry import CommandRegistry
from repl_toolkit.commands.base import BaseCommand
from .adapted_commands import AdaptedCommands
from ..backend import YacbaBackend

COMMAND_REGISTRY = {
    # Session management
    '/session': {
        'handler': 'adapters.repl_toolkit.commands.session_commands.SessionCommands',
        'category': 'Session Management',
        'description': 'Manage conversation sessions',
        'usage': [
            '/session - Show current session',
            '/session <name> - Switch to session',
            '/session _LIST - List all sessions'
        ]
    },
    '/clear': {
        'handler': 'adapters.repl_toolkit.commands.session_commands.SessionCommands',
        'category': 'Session Management',
        'description': 'Clear current conversation',
        'usage': ['/clear - Clear conversation history']
    },

    # Information commands
    '/history': {
        'handler': 'adapters.repl_toolkit.commands.info_commands.InfoCommands',
        'category': 'Information',
        'description': 'Show conversation history',
        'usage': ['/history - Display message history as JSON']
    },
    '/tools': {
        'handler': 'adapters.repl_toolkit.commands.info_commands.InfoCommands',
        'category': 'Information',
        'description': 'List available tools',
        'usage': ['/tools - Show currently loaded tools']
    },
    '/conversation-manager': {
        'handler': 'adapters.repl_toolkit.commands.info_commands.InfoCommands',
        'category': 'Information',
        'description': 'Show conversation manager configuration',
        'usage': ['/conversation-manager - Display current conversation '
                  'management settings']
    },
    '/conversation-stats': {
        'handler': 'adapters.repl_toolkit.commands.info_commands.InfoCommands',
        'category': 'Information',
        'description': 'Show conversation statistics',
        'usage': ['/conversation-stats - Display conversation memory '
                  'usage and statistics']
    }
}


class YacbaCommandRegistry(CommandRegistry):
    """Command registry that works with YacbaBackend."""

    def __init__(self, backend: YacbaBackend):
        super().__init__()
        self.backend = backend
        # Register YACBA-specific commands on top of basic repl_toolkit commands
        for command, config in COMMAND_REGISTRY.items():
            self.add_command(
                command=command,
                handler_class=config.get('handler'),  # Will be resolved dynamically
                category=config['category'],
                description=config['description'],
                usage=config['usage'][0] if isinstance(config['usage'], list) else config['usage']
            )

    def _instantiate_handler(self, command: str,
                             handler_class: Any) -> BaseCommand:
        """
        Instantiate a command handler class.

        Args:
            command: The command string (e.g., '/help')
            handler_class: The class to instantiate
        """
        if handler_class is None:
            return None

        if not issubclass(handler_class, AdaptedCommands):
            return super()._instantiate_handler(command, handler_class)

        # For adapted commands, pass the backend instance
        return handler_class(self, self.backend)