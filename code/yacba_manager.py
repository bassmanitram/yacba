"""
Manages the session persistence and orchestrates the core engine.
"""

import sys
from typing import List, Optional
from loguru import logger
from pathlib import Path

# Import our custom delegating session proxy
from delegating_session import DelegatingSession

from yacba_types.content import Message
from yacba_config import YacbaConfig
from yacba_engine import YacbaEngine


class ChatbotManager:
    """
    A context manager to handle session persistence (loading/saving history)
    and to manage the lifecycle of the core YacbaEngine.
    """
    
    def __init__(self, config: YacbaConfig):
        self.config = config
        self.engine: Optional[YacbaEngine] = None
        
        sessions_home = Path.home() / ".yacba" / "sessions"
        sessions_home.mkdir(parents=True, exist_ok=True)

        # Instantiate our delegating session proxy. This single object will be passed to the agent.
        self.session_manager: DelegatingSession = DelegatingSession(
            session_name=config.session_name,
            sessions_home=str(sessions_home)
        )
        logger.debug("ChatbotManager initialized with DelegatingSession.")

    def save_session(self) -> None:
        """
        Manually saves the agent's current history. Primarily used to confirm 
        a session has been set via the /save command, as the Agent now auto-saves.
        """
        if not self.session_manager.is_active:
            if not self.config.headless:
                print("No session name set. Use /save <name> to start a session.", file=sys.stderr)
            return

        if not self.engine or not self.engine.agent or not self.engine.agent.messages:
            logger.debug("Session history is empty. Nothing to save.")
            return
        
        try:
            # The agent saves automatically, but we can trigger one manually for immediate feedback.
            self.session_manager.save_messages(self.engine.agent.messages)
            if not self.config.headless:
                print("Session saved.")
            logger.info(f"Manual save triggered with {len(self.engine.agent.messages)} messages.")
            
        except IOError as e:
            error_msg = f"Error during manual save: {e}"
            logger.error(error_msg)
            if not self.config.headless:
                print(error_msg, file=sys.stderr)

    def clear_session(self) -> None:
        """
        Clears the agent's current message history and the persistent session file.
        """
        if self.engine and self.engine.agent:
            message_count = len(self.engine.agent.messages)
            self.engine.agent.messages.clear()
            logger.info(f"Cleared {message_count} messages from in-memory session history.")
        
        # This will clear the underlying file and deactivate the session
        self.session_manager.clear()
        
        if not self.config.headless:
            print("Conversation history and session file have been cleared.")

    def __enter__(self) -> 'ChatbotManager':
        """
        Initializes the engine with session history.
        """
        try:
            # Pass the single, persistent DelegatingSession instance to the engine.
            self.engine = YacbaEngine(
                config=self.config, 
                session_manager=self.session_manager
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
        No explicit save is needed here.
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
