"""
User interface components for YACBA CLI.

This package contains reusable UI components:
- Message display and formatting
- Tab completion
- Input session management
- Agent interaction utilities
- Callback handlers for output formatting
- Error handling and display
"""

from utils.startup_messages import print_welcome_message, print_startup_info
from .session import create_prompt_session
from .error_handling import format_error

__all__ = [
    # Message display
    'print_welcome_message',
    'print_startup_info',

    # Input handling
    'create_prompt_session',

    # Error handling
    'format_error',
]
