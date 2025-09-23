"""
Meta-command handlers for YACBA CLI.

This package contains handlers for all interactive meta-commands that users
can execute during a chat session. Each command type is organized into
focused modules for maintainability.

Command Categories:
- Help command: /help - comprehensive help system (separate module)
- Session commands: /session, /clear - manage conversation state
- Info commands: /history, /tools - display information
- Control commands: /exit, /quit - application control
"""

from .command_handler import CommandHandler
from .help_command import HelpCommand
from .session_commands import SessionCommands
from .info_commands import InfoCommands
from .base_command import BaseCommand

# Import individual command classes for advanced usage
__all__ = [
    # Main command handler
    'CommandHandler',
    
    # Command category handlers
    'HelpCommand',
    'SessionCommands',
    'InfoCommands',
    'BaseCommand',
]

# Command registry for validation and help generation
COMMAND_REGISTRY = {
    # Help system (special case)
    '/help': {
        'handler': 'HelpCommand',
        'description': 'Show help information',
        'usage': [
            '/help - Show all available commands',
            '/help <command> - Show detailed help for a specific command'
        ]
    },
    
    # Session management
    '/session': {
        'handler': 'SessionCommands',
        'description': 'Manage conversation sessions',
        'usage': [
            '/session - Show current session',
            '/session <name> - Switch to session',
            '/session _LIST - List all sessions'
        ]
    },
    '/clear': {
        'handler': 'SessionCommands', 
        'description': 'Clear current conversation',
        'usage': ['/clear - Clear conversation history']
    },
    
    # Information commands
    '/history': {
        'handler': 'InfoCommands',
        'description': 'Show conversation history',
        'usage': ['/history - Display message history as JSON']
    },
    '/tools': {
        'handler': 'InfoCommands',
        'description': 'List available tools',
        'usage': ['/tools - Show currently loaded tools']
    },
    
    # Control commands (handled directly by main loop)
    '/exit': {
        'handler': 'MainLoop',
        'description': 'Exit the application',
        'usage': ['/exit - Exit YACBA']
    },
    '/quit': {
        'handler': 'MainLoop', 
        'description': 'Exit the application',
        'usage': ['/quit - Exit YACBA']
    }
}

def get_command_help(command: str = None) -> str:
    """
    Get help text for a specific command or all commands.
    
    Args:
        command: Specific command to get help for, or None for all commands
        
    Returns:
        Formatted help text
    """
    if command and command in COMMAND_REGISTRY:
        cmd_info = COMMAND_REGISTRY[command]
        help_text = f"{command}: {cmd_info['description']}\n"
        for usage in cmd_info['usage']:
            help_text += f"  {usage}\n"
        return help_text.strip()
    
    # Return help for all commands
    help_text = "Available commands:\n"
    for cmd, info in COMMAND_REGISTRY.items():
        help_text += f"  {cmd:<12} - {info['description']}\n"
    
    help_text += "\nUse '/help <command>' for detailed usage information."
    return help_text

def validate_command(command: str) -> bool:
    """
    Validate if a command is supported.
    
    Args:
        command: Command to validate (e.g., '/help')
        
    Returns:
        True if command is supported, False otherwise
    """
    return command in COMMAND_REGISTRY
