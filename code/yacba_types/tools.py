"""
Tool-related type definitions for YACBA.

YACBA only needs to know about tool CONFIGURATION, not execution or protocols.
All tool invocation is handled by strands-agents.
"""

from typing import Dict, List, Any, Optional, Protocol, runtime_checkable, Union
from typing_extensions import TypedDict
from .base import JSONDict

# Tool configuration types (what YACBA manages)
class BaseToolConfig(TypedDict):
    """Base tool configuration that YACBA manages."""
    id: str
    type: str  # "mcp" or "python"
    disabled: bool

class MCPToolConfig(BaseToolConfig):
    """MCP tool configuration - YACBA only manages connection details."""
    # For stdio transport
    command: Optional[str]
    args: Optional[List[str]]
    env: Optional[Dict[str, str]]
    # For HTTP transport
    url: Optional[str]

class PythonToolConfig(BaseToolConfig):
    """Python tool configuration - YACBA only manages module loading."""
    module_path: str
    functions: List[str]

# Union of all tool config types
ToolConfig = Union[MCPToolConfig, PythonToolConfig]

# Protocol for tool objects (what strands provides to YACBA)
@runtime_checkable
class Tool(Protocol):
    """
    Protocol for tool objects that strands-agents provides.
    YACBA doesn't need to know implementation details.
    """
    tool_spec: Dict[str, Any]  # Generic spec, strands handles the details

# Tool loading result (what YACBA cares about)
class ToolLoadResult(TypedDict):
    """Result of tool loading operation."""
    tools: List[Tool]
    errors: List[str]
    config_id: str
