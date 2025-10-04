#  Command registry for validation and help generation
from typing import Any

from .session_commands import SessionCommands
from .info_commands import InfoCommands
from .adapted_commands import AdaptedCommands
from core.engine import YacbaEngine
from repl_toolkit.commands import CommandRegistry, BaseCommand

COMMAND_REGISTRY = {
    # : Session management
    '/session': {
        'handler_class': SessionCommands,
        'category': 'Session Management',
        'description': 'Manage conversation sessions',
        'usage': [
            '/session - List sessions',
            '/session <name> - Switch to session',
        ]
    },
    '/clear': {
        'handler_class': SessionCommands,
        'category': 'Session Management',
        'description': 'Clear current conversation',
        'usage': ['/clear - Clear conversation history']
    },

    #  : Information commands
    '/history': {
        'handler_class': InfoCommands,
        'category': 'Information',
        'description': 'Show conversation history',
        'usage': ['/history - Display message history as JSON']
    },
    '/tools': {
        'handler_class': InfoCommands,
        'category': 'Information',
        'description': 'List available tools',
        'usage': ['/tools - Show currently loaded tools']
    },
    '/conversation-manager': {
        'handler_class': InfoCommands,
        'category': 'Information',
        'description': 'Show conversation manager configuration',
        'usage': ['/conversation-manager - Display current conversation '
                  'management settings']
    },
    '/conversation-stats': {
        'handler_class': InfoCommands,
        'category': 'Information',
        'description': 'Show conversation statistics',
        'usage': ['/conversation-stats - Display conversation memory '
                  'usage and statistics']
    }
}


class YacbaCommandRegistry(CommandRegistry):
    """Utility class for command registry operations."""

    def __init__(self, engine: YacbaEngine):
        super().__init__()
        self.engine = engine
        self.commands.update(COMMAND_REGISTRY)

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

        #  : For adapted commands, pass the engine instance
        return handler_class(self, self.engine)
