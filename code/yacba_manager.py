# yacba_manager.py
# Manages the session persistence and orchestrates the core engine.

import os
import sys
import json
from typing import List, Dict, Any, Optional
from loguru import logger

from yacba_engine import YacbaEngine
from yacba_config import YacbaConfig


class ChatbotManager:
    """
    A context manager to handle session persistence (loading/saving history)
    and to manage the lifecycle of the core YacbaEngine.
    """
    def __init__(self, config: YacbaConfig):
        self.config = config
        self.session_filepath: Optional[str] = f"{config.session_name}.yacba-session.json" if config.session_name else None
        self.engine: Optional[YacbaEngine] = None
        logger.debug("ChatbotManager initialized.")

    def set_session_name(self, name: str):
        """Updates the session name and file path for the manager."""
        self.config.session_name = name
        self.session_filepath = f"{name}.yacba-session.json"

    def save_session(self):
        """Saves the current agent's message history to the session file."""
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
            print(f"Session saved to '{self.session_filepath}'.")
        except IOError as e:
            print(f"Error saving session to '{self.session_filepath}': {e}", file=sys.stderr)

    def clear_session(self):
        """Clears the agent's current message history."""
        if self.engine and self.engine.agent:
            self.engine.agent.messages.clear()
            print("Conversation history has been cleared.")

    def _load_session_if_exists(self) -> List[Dict[str, Any]]:
        """Loads a session from a file if it exists, otherwise returns an empty list."""
        if self.session_filepath and os.path.exists(self.session_filepath):
            try:
                with open(self.session_filepath, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
                    logger.info(f"Loaded {len(messages)} messages from session: {self.session_filepath}")
                    return messages
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Could not load or parse session file '{self.session_filepath}': {e}")
        return []

    def __enter__(self):
        """Initializes the engine with session history."""
        initial_messages = self._load_session_if_exists()
        self.engine = YacbaEngine(self.config, initial_messages)
        self.engine.startup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Saves session and shuts down the engine."""
        if not self.config.headless:
            self.save_session()
        
        if self.engine:
            self.engine.shutdown()
