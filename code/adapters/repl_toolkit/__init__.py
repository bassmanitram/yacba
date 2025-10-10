"""
Adapters for integrating repl_toolkit with YACBA.

This module provides the adapters needed to use repl_toolkit's
interactive and headless interfaces with YACBA's existing
command system and functionality.
"""

from .command_adapter import YacbaCommandAdapter

__all__ = [
    'YacbaCommandAdapter'
]