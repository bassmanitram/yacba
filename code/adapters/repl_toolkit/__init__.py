"""
Adapters for integrating repl_toolkit with YACBA.

This module provides the adapters needed to use repl_toolkit's
interactive and headless interfaces with YACBA's existing
command system and functionality.
"""

from .commands.registry import BackendCommandRegistry
from .completer import YacbaCompleter

__all__ = [
    'BackendCommandRegistry',
    'YacbaCompleter'
]