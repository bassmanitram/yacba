"""
CLI package for YACBA.

This package contains all command-line interface related functionality:
- User interface components (messages, completion, sessions)
- Execution modes (interactive and headless)
- Meta-command handlers
"""

# Import main CLI functions for easy access
from .interface import print_welcome_message, print_startup_info, YacbaCompleter
from .modes import chat_loop_async, run_headless_mode

# Import command handler for advanced usage
from .commands import CommandHandler

__all__ = [
    # Interface components
    'print_welcome_message',
    'print_startup_info', 
    'YacbaCompleter',
    
    # Execution modes
    'chat_loop_async',
    'run_headless_mode',
    
    # Command handling
    'CommandHandler',
]

# CLI package version
__version__ = '1.0.0'
