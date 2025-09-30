from contextlib import ExitStack
from typing import Any, Dict

from .python_adapter import PythonToolAdapter
from .mcp_adapters import MCPHTTPAdapter, MCPStdIOAdapter
from yacba_types.tools import ToolCreationResult
from .base_adapter import ToolAdapter
from loguru import logger


class ToolFactory:
    """A factory that uses registered adapters to create tools."""

    def __init__(self, exit_stack: ExitStack):
        self._adapters: Dict[str, ToolAdapter] = {
            "python": PythonToolAdapter(exit_stack),
            "mcp-stdio": MCPStdIOAdapter(exit_stack),
            "mcp-http": MCPHTTPAdapter(exit_stack)
        }

    def create_tools(self, config: Dict[str, Any]) -> ToolCreationResult:
        """Creates tools from a configuration dictionary."""
        tool_type = config.get("type")

        # Special handling for MCP to distinguish between stdio and http
        if tool_type == "mcp":
            if "command" in config:
                tool_type = "mcp-stdio"
            elif "url" in config:
                tool_type = "mcp-http"
            else:
                logger.error(f"MCP config for '{config.get('id')}' is missing 'url' or 'command'. Cannot connect.")
                return ToolCreationResult(
                    tools=[],
                    requested_functions=config.get("functions", []),
                    found_functions=[],
                    missing_functions=config.get("functions", []),
                    error="MCP config missing 'url' or 'command'"
                )

        adapter = self._adapters.get(tool_type)
        if adapter:
            return adapter.create(config)
        else:
            logger.warning(f"Tool '{config.get('id')}' has unknown type '{tool_type}'. Skipping.")
            return ToolCreationResult(
                tools=[],
                requested_functions=config.get("functions", []),
                found_functions=[],
                missing_functions=config.get("functions", []),
                error=f"Unknown tool type '{tool_type}'"
            )
