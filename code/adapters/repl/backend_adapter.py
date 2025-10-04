"""
Backend adapters for connecting YACBA engine to repl_toolkit.

These adapters implement repl_toolkit's backend protocols using YACBA's engine.
"""

from typing import TYPE_CHECKING

from repl_toolkit import AsyncBackend, HeadlessBackend

if TYPE_CHECKING:
    from core.engine import YacbaEngine


class YacbaAsyncBackend(AsyncBackend):
    """
    Adapter that implements repl_toolkit's AsyncBackend protocol using YACBA's engine.
    
    This allows YACBA's engine to be used with repl_toolkit's AsyncREPL interface.
    """
    
    def __init__(self, engine: "YacbaEngine"):
        """
        Initialize the backend adapter.
        
        Args:
            engine: YACBA engine instance
        """
        self.engine = engine
    
    async def handle_input(self, user_input: str) -> bool:
        """
        Process user input using YACBA's engine.
        
        Args:
            user_input: Input string from the user
            
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            # Use YACBA's engine to process the input
            # The engine's handle_input method should handle the response streaming
            await self.engine.handle_input(user_input)
            return True
        except Exception as e:
            # Log the error but let the REPL continue
            from loguru import logger
            logger.error(f"Error processing input in YACBA engine: {e}")
            return False


class YacbaHeadlessBackend(HeadlessBackend):
    """
    Adapter that implements repl_toolkit's HeadlessBackend protocol using YACBA's engine.
    
    This allows YACBA's engine to be used with repl_toolkit's headless mode.
    """
    
    def __init__(self, engine: "YacbaEngine"):
        """
        Initialize the headless backend adapter.
        
        Args:
            engine: YACBA engine instance
        """
        self.engine = engine
    
    async def handle_input(self, user_input: str) -> bool:
        """
        Process user input using YACBA's engine in headless mode.
        
        Args:
            user_input: Input string from the user
            
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            # Use YACBA's engine to process the input
            await self.engine.handle_input(user_input)
            return True
        except Exception as e:
            # Log the error and return failure
            from loguru import logger
            logger.error(f"Error processing input in YACBA engine (headless): {e}")
            return False