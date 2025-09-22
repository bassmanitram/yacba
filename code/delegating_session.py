# code/delegating_session.py
"""
A session proxy that implements the SessionManager protocol to allow for dynamic
session switching.
"""
from typing import Optional, List, Any
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
    _agent: Optional[Agent]

    def __init__(self, session_name: Optional[str], sessions_home: Optional[str | Path] = None):
        """Initializes the proxy, optionally setting the first active session."""
        super().__init__(session_id=session_name or "inactive")
        
        self._sessions_home = Path(sessions_home or Path.home() / ".yacba/strands/sessions")  # Default to ~/.yacba
        self._active_session = None
        self._agent = None
        self.session_id = session_name or "inactive"

    def set_active_session(self, session_name: str) -> None:
        """
        Creates and activates a new FileSessionManager. It then calls the new
        session's initialize() method to sync its history with the agent.
        """
        if not self._agent:
            logger.error("Cannot set active session: DelegatingSession has not been initialized with an agent yet.")
            return

        logger.info(f"Switching active session to '{session_name}'...")
        self.session_id = session_name
        
        new_session = FileSessionManager(session_id=session_name, storage_dir=str(self._sessions_home))
        new_session.initialize(self._agent)
        self._active_session = new_session
        
        logger.info(f"DelegatingSession is now active for session_id: '{self.session_id}'. Agent history has been updated.")

    def list_sessions(self) -> List[str]:
        """Scans the sessions directory and returns a list of available session names."""
        if not self._sessions_home.exists():
            return []
        
        # FileSessionManager saves files as in folders named "session_<name>"
        session_dirs = [p for p in self._sessions_home.iterdir() if p.is_dir() and p.name.startswith("session_")]
        session_names = [p.name[len("session_"):] for p in session_dirs]
        return sorted(session_names)

    @property
    def is_active(self) -> bool:
        """Returns True if a session is currently active."""
        return self._active_session is not None

    # --- Methods that implement the SessionManager abstract interface ---

    def initialize(self, agent: "Agent", **kwargs: Any) -> None:
        """Stores the agent instance and sets up the initial session if one was provided."""
        self._agent = agent
        if self.session_id != "inactive" and not self._active_session:
            self.set_active_session(self.session_id)

    def append_message(self, message: Message, agent: "Agent", **kwargs: Any) -> None:
        """Appends a single message to the active session."""
        if self._active_session:
            self._active_session.append_message(message, agent, **kwargs)

    def redact_latest_message(self, redact_message: Message, agent: "Agent", **kwargs: Any) -> None:
        """Redacts the latest message from the active session."""
        if self._active_session:
            self._active_session.redact_latest_message(redact_message, agent, **kwargs)
            
    def sync_agent(self, agent: Agent) -> None:
        """Syncs the agent's state with the active session."""
        if self._active_session:
            self._active_session.sync_agent(agent)

    def clear(self, agent: "Agent", **kwargs: Any) -> None:
        """
        Clears the agent's in-memory messages. If a session is active,
        it also clears the persisted session file by overwriting it with an
        empty history, keeping the session active.
        """
        # Step 1: Always clear the agent's in-memory message list.
        if agent and agent.messages:
            agent.messages.clear()
            logger.debug("Cleared agent's in-memory message list.")

        # Step 2: If a session is active, clear its persisted file data
        #
        # TBD: Decide if we want to delete the session file entirely instead of just clearing it.
        #
        #if self._active_session:
        #    # pylint: disable=protected-access
        #    self._active_session._save([])
        #    logger.info(f"Cleared session file for '{self.session_id}'. Session remains active.")

