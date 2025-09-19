"""
Manages the session persistence and orchestrates the core engine.
Migrated to use focused type system.
"""

import os
import sys
import json
from typing import List, Optional
from loguru import logger

# Import focused types
from yacba_types.content import Message
from yacba_config import YacbaConfig
from yacba_engine import YacbaEngine


class ChatbotManager:
    """
    A context manager to handle session persistence (loading/saving history)
    and to manage the lifecycle of the core YacbaEngine.
    
    YACBA's responsibilities:
    - Session file management and persistence
    - Engine lifecycle management
    - Configuration validation and setup
    """
    
    def __init__(self, config: YacbaConfig):
        self.config = config
        self.session_filepath: Optional[str] = (
            f"{config.session_name}.yacba-session.json" 
            if config.session_name else None
        )
        self.engine: Optional[YacbaEngine] = None
        logger.debug("ChatbotManager initialized.")

    def set_session_name(self, name: str) -> None:
        """
        Updates the session name and file path for the manager.
        
        Args:
            name: New session name
        """
        self.config.session_name = name
        self.session_filepath = f"{name}.yacba-session.json"
        logger.debug(f"Session name updated to: {name}")

    def save_session(self) -> None:
        """
        Saves the current agent's message history to the session file.
        YACBA's responsibility: Session persistence.
        """
        if not self.session_filepath:
            if not self.config.headless:
                print("No session name set. Use --session-name <name> or /save <name> to start a session.", file=sys.stderr)
            return

        if not self.engine or not self.engine.agent or not self.engine.agent.messages:
            logger.debug("Session history is empty. Nothing to save.")
            return
        
        try:
            with open(self.session_filepath, 'w', encoding='utf-8') as f:
                json.dump(self.engine.agent.messages, f, indent=2, ensure_ascii=False)
            
            if not self.config.headless:
                print(f"Session saved to '{self.session_filepath}'.")
            logger.info(f"Session saved to '{self.session_filepath}' with {len(self.engine.agent.messages)} messages.")
            
        except IOError as e:
            error_msg = f"Error saving session to '{self.session_filepath}': {e}"
            logger.error(error_msg)
            if not self.config.headless:
                print(error_msg, file=sys.stderr)

    def clear_session(self) -> None:
        """
        Clears the agent's current message history.
        YACBA's responsibility: Session management.
        """
        if self.engine and self.engine.agent:
            message_count = len(self.engine.agent.messages)
            self.engine.agent.messages.clear()
            logger.info(f"Cleared {message_count} messages from session history.")
            if not self.config.headless:
                print("Conversation history has been cleared.")

    def _load_session_if_exists(self) -> List[Message]:
        """
        Loads a session from a file if it exists, otherwise returns an empty list.
        YACBA's responsibility: Session loading and validation.
        
        Returns:
            List of messages from the session file
        """
        if not self.session_filepath or not os.path.exists(self.session_filepath):
            return []
        
        try:
            with open(self.session_filepath, 'r', encoding='utf-8') as f:
                messages = json.load(f)
                
            # Basic validation of loaded messages
            if not isinstance(messages, list):
                logger.error(f"Invalid session file format in '{self.session_filepath}': expected list of messages")
                return []
            
            # Validate message structure
            valid_messages = []
            for i, msg in enumerate(messages):
                if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                    logger.warning(f"Skipping invalid message {i} in session file")
                    continue
                valid_messages.append(msg)
            
            logger.info(f"Loaded {len(valid_messages)} messages from session: {self.session_filepath}")
            return valid_messages
            
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Could not load or parse session file '{self.session_filepath}': {e}")
            return []

    def __enter__(self) -> 'ChatbotManager':
        """
        Initializes the engine with session history.
        YACBA's responsibility: Engine initialization and configuration.
        
        Returns:
            Self for context manager usage
        """
        try:
            # Load session history if available
            initial_messages = self._load_session_if_exists()
            
            # Create and initialize the engine
            self.engine = YacbaEngine(self.config, initial_messages)
            
            # Start the engine
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
        Saves session and shuts down the engine.
        YACBA's responsibility: Cleanup and persistence.
        
        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred  
            exc_tb: Exception traceback if an exception occurred
        """
        try:
            # Save session if not in headless mode
            if not self.config.headless:
                self.save_session()
            
            # Shutdown the engine
            if self.engine:
                self.engine.shutdown()
                
            logger.info("ChatbotManager context exited successfully")
            
        except Exception as e:
            logger.error(f"Error during ChatbotManager cleanup: {e}")

    @property
    def is_ready(self) -> bool:
        """Check if the manager and engine are ready for use."""
        return self.engine is not None and self.engine.is_ready

    @property
    def session_info(self) -> str:
        """Get information about the current session."""
        if not self.session_filepath:
            return "No session"
        
        message_count = 0
        if self.engine and self.engine.agent:
            message_count = len(self.engine.agent.messages)
        
        return f"Session: {self.config.session_name} ({message_count} messages)"
