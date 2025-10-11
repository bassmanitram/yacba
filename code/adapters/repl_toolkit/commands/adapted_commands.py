"""
Adapted commands for the CLI interface.

This module provides commands that have been adapted to work with the CLI
interface while maintaining compatibility with the underlying system.
"""

from repl_toolkit.commands.base import BaseCommand
from ..backend import YacbaBackend


class AdaptedCommands(BaseCommand):
    """Commands that have been adapted for CLI use with YacbaBackend."""
    
    def __init__(self, registry, backend: YacbaBackend):
        super().__init__(registry)
        self.backend = backend