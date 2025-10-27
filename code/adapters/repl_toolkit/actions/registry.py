"""Action registry for YACBA CLI integration."""
from typing import TYPE_CHECKING
from loguru import logger

from repl_toolkit import ActionRegistry
from .session_actions import register_session_actions
from .info_actions import register_info_actions

class YacbaActionRegistry(ActionRegistry):
    """Action registry that integrates YACBA-specific actions with repl-toolkit."""

    def __init__(self):
        # Pass backend to parent constructor - it will handle backend injection
        super().__init__()
        
        # Register YACBA-specific actions
        logger.debug("Registering YACBA actions")
        register_session_actions(self)
        register_info_actions(self)
        logger.debug(f"Registered {len(self.actions)} total actions")