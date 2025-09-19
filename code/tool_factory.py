# tool_factory.py
# A factory for creating and managing different types of tools.

import os
import importlib
import importlib.util
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from contextlib import ExitStack

from loguru import logger
from strands.tools.mcp import MCPClient
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client


class ToolAdapter(ABC):
    """Abstract base class for a tool adapter."""
    def __init__(self, exit_stack: ExitStack):
        self.exit_stack = exit_stack

    @abstractmethod
    def create(self, config: Dict[str, Any]) -> List[Any]:
        """Creates a tool or tools based on the provided configuration."""
        pass


class MCPStdIOAdapter(ToolAdapter):
    """Adapter for creating MCP tools from a stdio command."""
    def create(self, config: Dict[str, Any]) -> List[Any]:
        server_id = config.get("id", "unknown-stdio-server")
        logger.debug(f"Starting MCP server '{server_id}' with command: {config.get('command')}")
        
        process_env = os.environ.copy()
        if 'env' in config:
            process_env.update(config['env'])
        
        params = StdioServerParameters(command=config["command"], args=config.get("args", []), env=process_env)
        client_factory = lambda: stdio_client(params)
        
        try:
            client = self.exit_stack.enter_context(MCPClient(client_factory))
            tools = client.list_tools_sync()
            logger.info(f"Successfully loaded {len(tools)} tools from MCP server: {server_id}")
            return tools
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_id}: {e}")
            return []


class MCPHTTPAdapter(ToolAdapter):
    """Adapter for creating MCP tools from an HTTP endpoint."""
    def create(self, config: Dict[str, Any]) -> List[Any]:
        server_id = config.get("id", "unknown-http-server")
        url = config.get("url")
        logger.debug(f"Connecting to MCP server '{server_id}' via HTTP at {url}")
        
        client_factory = lambda: streamablehttp_client(url)
        
        try:
            client = self.exit_stack.enter_context(MCPClient(client_factory))
            tools = client.list_tools_sync()
            logger.info(f"Successfully loaded {len(tools)} tools from MCP server: {server_id}")
            return tools
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_id}: {e}")
            return []


class PythonToolAdapter(ToolAdapter):
    """Adapter for creating tools from local or installed Python modules."""
    def create(self, config: Dict[str, Any]) -> List[Any]:
        tool_id, module_path, func_names, src_file = (config.get(k) for k in ["id", "module_path", "functions", "source_file"])
        if not all([tool_id, module_path, func_names, src_file]):
            logger.warning(f"Python tool config is missing required fields. Skipping.")
            return []

        resolved_path = os.path.abspath(os.path.join(os.path.dirname(src_file), module_path))
        
        module = self._load_module(tool_id, module_path, resolved_path)
        if not module:
            return []

        try:
            loaded_tools = []
            
            # Only look for the specific function names requested in the config
            for name in func_names:
                if not isinstance(name, str):
                    logger.warning(f"Function name '{name}' is not a string in tool config '{tool_id}'. Skipping.")
                    continue
                    
                obj = getattr(module, name, None)
                if obj is None:
                    logger.warning(f"Function '{name}' not found in module '{module_path}'. Skipping.")
                    continue
                    
                # Check if it's a valid Strands tool (has tool_spec attribute)
                if hasattr(obj, 'tool_spec') and callable(obj):
                    loaded_tools.append(obj)
                    logger.debug(f"Successfully loaded tool function '{name}' from module '{module_path}'")
                else:
                    logger.warning(f"Object '{name}' in module '{module_path}' is not a valid Strands tool (missing tool_spec or not callable). Skipping.")
            
            logger.info(f"Successfully loaded {len(loaded_tools)} tools from Python module: {tool_id}")
            return loaded_tools
        except Exception as e:
            logger.error(f"Failed to extract tools from Python module '{tool_id}': {e}")
            return []

    def _load_module(self, tool_id: str, module_path: str, resolved_path: str) -> Optional[Any]:
        """Loads a module from a file path or a package path."""
        # First, try to load as a local file for backward compatibility
        if os.path.exists(resolved_path):
            logger.debug(f"Attempting to load Python tool '{tool_id}' from file: {resolved_path}")
            try:
                spec = importlib.util.spec_from_file_location(name=tool_id, location=resolved_path)
                if not spec or not spec.loader: 
                    raise ImportError("Could not create module spec.")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
            except Exception as e:
                logger.error(f"Failed to load Python module from file '{resolved_path}': {e}")
                return None
        # If not a file, fall back to loading as an installed package
        else:
            logger.debug(f"Attempting to load Python tool '{tool_id}' from package: {module_path}")
            try:
                return importlib.import_module(module_path)
            except ModuleNotFoundError:
                logger.error(f"Python module for tool '{tool_id}' not found as a local file at '{resolved_path}' or as an installed package '{module_path}'.")
                return None
            except Exception as e:
                logger.error(f"Failed to import Python module package '{module_path}': {e}")
                return None


class ToolFactory:
    """A factory that uses registered adapters to create tools."""
    def __init__(self, exit_stack: ExitStack):
        self._adapters: Dict[str, ToolAdapter] = {
            "python": PythonToolAdapter(exit_stack),
            "mcp-stdio": MCPStdIOAdapter(exit_stack),
            "mcp-http": MCPHTTPAdapter(exit_stack)
        }

    def create_tools(self, config: Dict[str, Any]) -> List[Any]:
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
                return []

        adapter = self._adapters.get(tool_type)
        if adapter:
            return adapter.create(config)
        else:
            logger.warning(f"Tool '{config.get('id')}' has unknown type '{tool_type}'. Skipping.")
            return []
