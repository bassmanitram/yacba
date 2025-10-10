"""
Command adapter for integrating YACBA commands with repl_toolkit.

This adapter bridges YACBA's existing BackendCommandRegistry with
repl_toolkit's CommandHandler protocol.
"""

from typing import Optional
from loguru import logger

from repl_toolkit.ptypes import CommandHandler
from adapters.cli.commands.registry import BackendCommandRegistry
from adapters.strands_factory.backend_adapter import YacbaStrandsBackend


class YacbaCommandAdapter:
    """
    Adapter that wraps YACBA's BackendCommandRegistry to implement
    repl_toolkit's CommandHandler protocol.
    
    This allows YACBA's existing sophisticated command system to work
    seamlessly with repl_toolkit's AsyncREPL interface.
    """
    
    def __init__(self, backend: YacbaStrandsBackend):
        """
        Initialize the command adapter.
        
        Args:
            backend: The YACBA strands backend adapter
        """
        self.backend = backend
        # Create the YACBA command registry with the agent proxy
        self.command_registry = BackendCommandRegistry(backend.get_agent_proxy())
        logger.debug("Initialized YacbaCommandAdapter with BackendCommandRegistry")
    
    async def handle_command(self, command: str) -> None:
        """
        Handle a command string using YACBA's command system.
        
        Args:
            command: The full command string including the leading '/'
        """
        if not command.startswith('/'):
            logger.warning(f"Command does not start with '/': {command}")
            return
        
        # Remove the leading '/' for YACBA's command system
        command_name = command[1:].strip()
        
        if not command_name:
            logger.debug("Empty command, ignoring")
            return
        
        logger.debug(f"Processing command: /{command_name}")
        
        try:
            # Use YACBA's existing command processing
            await self.command_registry.handle_command(command_name)
        except Exception as e:
            logger.error(f"Error processing command '/{command_name}': {e}")
            print(f"Error executing command: {e}")
    
    def list_commands(self) -> list[str]:
        """
        Get a list of available commands.
        
        Returns:
            list[str]: List of available command names (without '/' prefix)
        """
        try:
            return self.command_registry.list_commands()
        except Exception as e:
            logger.error(f"Error listing commands: {e}")
            return []
    
    def get_command_help(self, command_name: str) -> Optional[str]:
        """
        Get help text for a specific command.
        
        Args:
            command_name: Name of the command (without '/' prefix)
            
        Returns:
            Optional[str]: Help text for the command, or None if not found
        """
        try:
            # This depends on YACBA's command registry having help functionality
            if hasattr(self.command_registry, 'get_command_help'):
                return self.command_registry.get_command_help(command_name)
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting help for command '{command_name}': {e}")
            return None