"""
Meta-command handlers for YACBA CLI.

This package contains handlers for all interactive meta-commands that users
can execute during a chat session. Each command type is organized into
focused modules for maintainability.

"""

from .registry import CommandRegistry
__all__ = [
    # Command registry
    'CommandRegistry',
]
