"""
Adapted commands for the CLI interface.

This module provides commands that have been adapted to work with the CLI
interface while maintaining compatibility with the underlying system.
"""

from repl_toolkit.commands.base import BaseCommand
from ...strands_factory.backend_adapter import YacbaStrandsBackend


class AdaptedCommands(BaseCommand):
    """Commands that have been adapted for CLI use with YacbaStrandsBackend."""
    
    def __init__(self, registry, backend: YacbaStrandsBackend):
        super().__init__(registry)
        self.backend = backend