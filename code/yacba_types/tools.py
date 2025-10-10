"""
Tool-related type definitions for YACBA.

YACBA only needs to know about tool CONFIGURATION, not execution or protocols.
All tool invocation is handled by strands-agents.
"""

from typing import Dict, List, Any, Optional, Protocol, runtime_checkable, Union
from typing_extensions import TypedDict, NamedTuple

from .config import ToolDiscoveryResult
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
    pass  # Removed tool_spec requirement as it's unreliable

# Unified tool processing result


class ToolProcessingResult(NamedTuple):
    """
    Unified result for all tool processing operations.
    Consolidates discovery, loading, and execution results.
    """
    config_id: str
    source_file: str
    success: bool
    tools: List[Any]  # Successfully loaded tools
    requested_functions: List[str]  # Functions that were requested (for Python tools)
    found_functions: List[str]      # Functions that were actually found
    missing_functions: List[str]    # Functions that were requested but not found
    error_message: Optional[str]    # Human-readable error description

    @property
    def has_tools(self) -> bool:
        """Check if any tools were successfully loaded."""
        return len(self.tools) > 0

    @property
    def has_missing_functions(self) -> bool:
        """Check if any requested functions were missing."""
        return len(self.missing_functions) > 0

    @property
    def has_error(self) -> bool:
        """Check if there was an error during processing."""
        return self.error_message is not None


class ToolCreationResult(NamedTuple):
    """Detailed result of tool creation with missing function tracking."""
    tools: List[Any]
    requested_functions: List[str]  # Functions that were requested
    found_functions: List[str]      # Functions that were actually found
    missing_functions: List[str]    # Functions that were requested but not found
    error: Optional[str]

# Overall tool system status


class ToolSystemStatus(NamedTuple):
    """Overall status of the tool system after full initialization."""
    discovery_result: ToolDiscoveryResult
    processing_results: List[ToolProcessingResult]
    total_tools_loaded: int

    @property
    def successful_results(self) -> List[ToolProcessingResult]:
        """Get all successful tool processing results."""
        return [r for r in self.processing_results if r.success and r.has_tools]

    @property
    def failed_results(self) -> List[ToolProcessingResult]:
        """Get all failed tool processing results."""
        return [r for r in self.processing_results if not r.success or r.has_error]

    @property
    def results_with_missing_functions(self) -> List[ToolProcessingResult]:
        """Get results that have missing requested functions."""
        return [r for r in self.processing_results if r.has_missing_functions]