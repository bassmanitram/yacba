# code/delegating_session.py
"""
A session proxy that implements the SessionManager protocol to allow for dynamic
session switching.
"""
from typing import Optional, List, Dict, Any
from pathlib import Path
from loguru import logger

from strands import Agent
from strands.session.session_manager import SessionManager
from strands.session.file_session_manager import FileSessionManager
from strands.types.content import Message

class DelegatingSession(SessionManager):
    """
    A session proxy that holds a real, switchable FileSessionManager object internally.
    This allows the active session to be changed mid-flight. It adheres to the
    SessionManager interface, making it compatible with the strands.Agent.
    """
    _active_session: Optional[FileSessionManager]
    _agent: Optional[Agent] # Add a placeholder for the agent instance

    def __init__(self, session_name: Optional[str], sessions_home: str | Path):
        """Initializes the proxy, optionally setting the first active session."""
        super().__init__(session_id=session_name or "inactive")
        
        self._sessions_home = str(sessions_home)
        self._active_session = None
        self._agent = None # Initialize agent as None
        self.session_id = session_name or "inactive"
        
        # Note: We cannot create the initial session here because we don't have the agent yet.
        # It will be created during the first `initialize` call.

    def set_active_session(self, session_name: str) -> None:
        """
        Creates and activates a new FileSessionManager. Crucially, it then calls
        the new session's initialize() method to sync its history with the agent,
        effectively loading the new session.
        """
        if not self._agent:
            logger.error("Cannot set active session: DelegatingSession has not been initialized with an agent yet.")
            return

        logger.info(f"Switching active session to '{session_name}'...")
        self.session_id = session_name
        
        # 1. Create the new concrete session manager
        new_session = FileSessionManager(session_id=session_name, sessions_home=self._sessions_home)
        
        # 2. **CRITICAL STEP**: Initialize the new session with the agent.
        #    This triggers the sync_agent() method, which loads the history
        #    from the file and replaces the agent's current message list.
        new_session.initialize(self._agent)
        
        # 3. Assign the fully initialized and synced session as the active one.
        self._active_session = new_session
        
        logger.info(f"DelegatingSession is now active for session_id: '{self.session_id}'. Agent history has been updated.")

    @property
    def is_active(self) -> bool:
        """Returns True if a session is currently active."""
        return self._active_session is not None

    # --- Methods that implement the SessionManager abstract interface ---

    def initialize(self, agent: "Agent", **kwargs: Any) -> None:
        """
        Initializes the session. This is the first point where we get access
        to the agent instance.
        """
        # Store the agent instance for future use (like session switching)
        self._agent = agent

        # If a session name was provided at startup, create and initialize it now.
        if self.session_id != "inactive" and not self._active_session:
            self.set_active_session(self.session_id)
        
        # The parent call is no longer needed as set_active_session handles initialization.
        # super().initialize(agent, **kwargs)

    def append_message(self, message: Message, agent: "Agent", **kwargs: Any) -> None:
        """Appends a single message to the session."""
        if self._active_session:
            self._active_session.append_message(message, agent, **kwargs)

    def redact_latest_message(self, redact_message: Message, agent: "Agent", **kwargs: Any) -> None:
        """Redacts the latest message from the session."""
        if self._active_session:
            self._active_session.redact_latest_message(redact_message, agent, **kwargs)
            
    def sync_agent(self, agent: Agent) -> None:
        """Syncs the agent's state with the session."""
        if self._active_session:
            self._active_session.sync_agent(agent)

