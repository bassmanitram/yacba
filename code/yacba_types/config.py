"""
Configuration-related type definitions for YACBA.

YACBA manages configuration, not tool execution or protocol details.
"""

from typing import Dict, List, Any, Optional, Literal, Union
from typing_extensions import TypedDict
from .base import JSONDict, PathLike

# Model configuration types (what YACBA passes to model frameworks)
class ModelConfig(TypedDict, total=False):
    """Type definition for model configuration parameters."""
    temperature: float
    max_tokens: int
    top_p: float
    top_k: int
    stop: List[str]
    presence_penalty: float
    frequency_penalty: float
    # Framework-specific fields (YACBA just passes these through)
    safety_settings: List[Dict[str, Any]]
    response_format: Dict[str, Any]

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

# Session data types (what YACBA persists)
class SessionMessage(TypedDict):
    """Type definition for session message."""
    role: Literal["user", "assistant", "system"]
    content: Any  # Can be string or list of content blocks

SessionData = List[SessionMessage]

# File upload types (what YACBA processes at startup)
class FileUpload(TypedDict):
    """Type definition for file upload information."""
    path: PathLike
    mimetype: str
    size: Optional[int]
