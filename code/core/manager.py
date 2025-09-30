"""
Resource manager to orchestrates the core engine.
"""

from typing import Optional
from loguru import logger

from .config import YacbaConfig
from .engine import YacbaEngine


class ChatbotManager:
    """
    A context manager to manage the lifecycle of the core YacbaEngine.
    """

    def __init__(self, config: YacbaConfig):
        self.config = config
        self.engine: Optional[YacbaEngine] = None

    def __enter__(self) -> 'ChatbotManager':
        """
        Initializes the engine with the provided configuration.
        """
        try:
            # Pass the single, persistent DelegatingSession instance to the engine.
            # It starts inactive; the agent will call its initialize() method.
            self.engine = YacbaEngine(
                config=self.config
            )

            if not self.engine.startup():
                logger.error("Failed to start YACBA engine")
                raise RuntimeError("Engine startup failed")

            logger.info("ChatbotManager context entered successfully")
            return self

        except Exception as e:
            logger.error(f"Failed to initialize ChatbotManager: {e}")
            if self.engine:
                self.engine.shutdown()
            raise

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Shuts down the engine. Auto-saving is now handled by the Agent via the session proxy.
        """
        try:
            if self.engine:
                self.engine.shutdown()
            logger.info("ChatbotManager context exited successfully")
        except Exception as e:
            logger.error(f"Error during ChatbotManager cleanup: {e}")

    @property
    def is_ready(self) -> bool:
        """Check if the manager and engine are ready for use."""
        return self.engine is not None and self.engine.is_ready
