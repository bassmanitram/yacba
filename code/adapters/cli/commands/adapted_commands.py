"""
Adapted commands for the CLI interface.

This module provides commands that have been adapted to work with the CLI
interface while maintaining compatibility with the underlying system.
"""



from cli.commands.base_command import BaseCommand


class AdaptedCommands(BaseCommand):
    """Commands that have been adapted for CLI use."""
    def __init__(self, registry, engine):
        super().__init__(registry)
        self.engine = engine

