"""Action registry for YACBA CLI integration."""
from typing import TYPE_CHECKING, Callable
from loguru import logger

from repl_toolkit import ActionRegistry
from .session_actions import register_session_actions
from .info_actions import register_info_actions
from .status_action import register_status_actions

class YacbaActionRegistry(ActionRegistry):
    """Action registry that integrates YACBA-specific actions with repl-toolkit."""

    def __init__(self, printer: Callable[[str], None] = print):
        """
        Initialize the YACBA action registry.
        
        Args:
            printer: Function to use for printing output. Defaults to print.
                     Use a stdout-based printer for headless mode.
        """
        # Pass printer to parent constructor
        super().__init__(printer=printer)
        
        # Register YACBA-specific actions
        logger.debug("Registering YACBA actions")
        register_session_actions(self)
        register_info_actions(self)
        register_status_actions(self)
        logger.debug(f"Registered {len(self.actions)} total actions")
