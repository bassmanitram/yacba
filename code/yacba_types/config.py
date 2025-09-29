"""
Configuration-related type definitions for YACBA.

YACBA manages configuration, not tool execution or protocol details.
"""

from typing import Dict, List, Any, Optional, Literal, Union
from typing_extensions import TypedDict, NamedTuple
from .base import JSONDict, PathLike

# Tool configuration types (what YACBA manages for tool loading)
ToolType = Literal["mcp", "python"]

class BaseToolConfig(TypedDict):
    """Base tool configuration."""
    id: str
    type: ToolType
    disabled: bool

class MCPToolConfig(BaseToolConfig):
    """MCP tool configuration - connection details only."""
    # For stdio transport
    command: Optional[str]
    args: Optional[List[str]]
    env: Optional[Dict[str, str]]
    # For HTTP transport
    url: Optional[str]

class PythonToolConfig(BaseToolConfig):
    """Python tool configuration - module loading details only."""
    module_path: str
    functions: List[str]

ToolConfig = Union[MCPToolConfig, PythonToolConfig]

# Discovery phase result (configuration file scanning)
class ToolDiscoveryResult(NamedTuple):
    """Result of scanning for tool configuration files."""
    successful_configs: List[ToolConfig]
    failed_configs: List[Dict[str, Any]]  # Include file path and error details
    total_files_scanned: int
    
    @property
    def has_failures(self) -> bool:
        """Check if any configuration files failed to load."""
        return len(self.failed_configs) > 0

# File upload types (what YACBA processes at startup)
class FileUpload(TypedDict):
    """Type definition for file upload information."""
    path: PathLike
    mimetype: str
    size: Optional[int]
