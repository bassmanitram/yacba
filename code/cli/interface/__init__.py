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

from .messages import print_welcome_message, print_startup_info
from .completer import YacbaCompleter
from .session import create_prompt_session
from .agent_interaction import handle_agent_stream, send_message_to_agent
from .callback_handler import YacbaCallbackHandler
from .error_handling import format_error

__all__ = [
    # Message display
    'print_welcome_message',
    'print_startup_info', 
    
    # Input handling
    'YacbaCompleter',
    'create_prompt_session',
    
    # Agent interaction
    'handle_agent_stream',
    'send_message_to_agent',
    
    # Callback handlers
    'YacbaCallbackHandler',
    
    # Error handling
    'format_error',
]
