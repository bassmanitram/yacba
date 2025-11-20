"""
Session and history path utilities.

Provides consistent path handling for session directories and history files,
ensuring YACBA history and strands session data are co-located.
"""

from pathlib import Path
from typing import Optional


def get_sessions_home() -> Path:
    """
    Get the base directory for strands sessions.

    Returns:
        Path: Base directory where all sessions are stored
              (~/.yacba/strands/sessions/)
    """
    return Path.home() / ".yacba" / "strands" / "sessions"


def get_session_directory(session_name: str) -> Path:
    """
    Get the full session directory path for a given session name.

    This directory contains both strands session data AND YACBA history file.
    Follows strands' naming convention: session_{name}

    Args:
        session_name: Name of the session

    Returns:
        Path: Full path to session directory
              (~/.yacba/strands/sessions/session_{name}/)
    """
    return get_sessions_home() / f"session_{session_name}"


def get_history_path(session_name: Optional[str]) -> Path:
    """
    Get the history file path for REPL command history.

    Args:
        session_name: Session name, or None for default history

    Returns:
        Path: Path to history file
              - With session: ~/.yacba/session_{session_name}_history.txt
              - Without session: ~/.yacba/history.txt
    """
    if session_name:
        return Path.home() / ".yacba" / f"session_{session_name}_history.txt"
    else:
        return Path.home() / ".yacba" / "history.txt"
