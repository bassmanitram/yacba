"""
Configuration-related type definitions for YACBA.

YACBA manages configuration, not tool execution or protocol details.
"""

from typing import Dict, List, Any
from typing_extensions import TypedDict, NamedTuple
from .base import PathLike


# Discovery phase result (configuration file scanning)


class ToolDiscoveryResult(NamedTuple):
    """Result of scanning for tool configuration files."""
    successful_configs: List[Dict[str, Any]]  # List of config dicts with file paths
    failed_configs: List[Dict[str, Any]]  # Include file path and error details
    total_files_scanned: int

    @property
    def has_failures(self) -> bool:
        """Check if any configuration files failed to load."""
        return len(self.failed_configs) > 0


# Session data type (what YACBA persists)


class SessionData(TypedDict):
    """Session data that YACBA persists to disk."""
    messages: List[Dict[str, Any]]
    metadata: Dict[str, Any]


# File upload types (what YACBA processes at startup)


class FileUpload(TypedDict):
    """Type definition for file upload information."""
    path: PathLike
    mimetype: str
    size: int
