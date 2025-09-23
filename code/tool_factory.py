# tool_factory.py
# A factory for creating and managing different types of tools.

import os
import importlib
import importlib.util
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, NamedTuple, Callable
from contextlib import ExitStack

from exceptiongroup import catch
from loguru import logger
from strands.tools.mcp import MCPClient
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

def _load_module_attribute(
    base_module: str,
    function: str,
    package_path: Optional[str] = None,
    base_path: Optional[str] = None,
) -> Callable:
    """
    Dynamically loads a function, using a specific directory as the root if provided.

    Args:
        base_module: The first part of the module's dotted path (e.g., 'my_app.lib').
        function: The second part of the path, including submodules and the
                  function name (e.g., 'utils.helpers.my_func').
        package_path: (Optional) The absolute path to a directory that should be
                      treated as the root for the import. If None, Python's
                      standard import search paths (sys.path) are used.

    Returns:
        A reference to the dynamically loaded function.
    """
    # 1. Combine the inputs into a full dotted path and separate module from function
    full_function_path = f"{base_module}.{function}"
    try:
        full_module_path, function_name = full_function_path.rsplit('.', 1)
        logger.debug(f"Loading function '{function_name}' from module '{full_module_path}' (package_path='{base_path}, package_path='{package_path}')")
    except ValueError as e:
        raise ValueError(f"Invalid path '{full_function_path}'.") from e

    # 2. Decide which loading strategy to use
    if package_path:
        # --- SCENARIO 1: Custom path is provided ---
        # Translate dotted module path to a relative file path
        relative_file_path = full_module_path.replace('.', os.path.sep) + '.py'
        absolute_file_path = os.path.join(base_path or "", package_path, relative_file_path)

        if not os.path.isfile(absolute_file_path):
            raise FileNotFoundError(f"Module file not found at: {absolute_file_path}")

        # Load the module directly from its file path without using sys.path
        spec = importlib.util.spec_from_file_location(full_module_path, absolute_file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {absolute_file_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

    else:
        # --- SCENARIO 2: Default behavior ---
        # Use Python's standard import mechanism, which searches sys.path
        try:
            module = importlib.import_module(full_module_path)
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                f"Module '{full_module_path}' not found in standard Python paths."
            ) from e
    # 3. Retrieve the function from the loaded module
    try:
        function_ref = getattr(module, function_name)
    except AttributeError as e:
        raise AttributeError(
            f"Function '{function_name}' not found in module '{full_module_path}'."
        ) from e

    return function_ref


class ToolCreationResult(NamedTuple):
    """Detailed result of tool creation with missing function tracking."""
    tools: List[Any]
    requested_functions: List[str]  # Functions that were requested
    found_functions: List[str]      # Functions that were actually found
    missing_functions: List[str]    # Functions that were requested but not found
    error: Optional[str]

class ToolAdapter(ABC):
    """Abstract base class for a tool adapter."""
    def __init__(self, exit_stack: ExitStack):
        self.exit_stack = exit_stack

    @abstractmethod
    def create(self, config: Dict[str, Any]) -> ToolCreationResult:
        """Creates a tool or tools based on the provided configuration."""
        pass


class MCPStdIOAdapter(ToolAdapter):
    """Adapter for creating MCP tools from a stdio command."""
    def create(self, config: Dict[str, Any]) -> ToolCreationResult:
        server_id = config.get("id", "unknown-stdio-server")
        logger.debug(f"Starting MCP server '{server_id}' with command: {config.get('command')}")
        
        process_env = os.environ.copy()
        if 'env' in config:
            process_env.update(config['env'])
        
        params = StdioServerParameters(command=config["command"], args=config.get("args", []), env=process_env)
        client_factory = lambda: stdio_client(params)
        
        try:
            client = self.exit_stack.enter_context(MCPClient(client_factory))
            all_tools = client.list_tools_sync()
            
            # Check if specific functions were requested
            requested_functions = config.get("functions", [])
            if requested_functions:
                # Filter tools to only include requested functions
                available_tool_names = [tool.tool_spec.get('name', '') for tool in all_tools if hasattr(tool, 'tool_spec')]
                found_functions = []
                filtered_tools = []
                
                for requested_func in requested_functions:
                    found = False
                    for tool in all_tools:
                        if hasattr(tool, 'tool_spec') and tool.tool_spec.get('name') == requested_func:
                            filtered_tools.append(tool)
                            found_functions.append(requested_func)
                            found = True
                            break
                    if not found:
                        logger.warning(f"MCP server '{server_id}' does not provide requested function '{requested_func}'")
                
                missing_functions = [f for f in requested_functions if f not in found_functions]
                tools_to_return = filtered_tools
            else:
                # No specific functions requested, return all tools
                requested_functions = []
                found_functions = [tool.tool_spec.get('name', 'unnamed') for tool in all_tools if hasattr(tool, 'tool_spec')]
                missing_functions = []
                tools_to_return = all_tools
            
            logger.info(f"Successfully loaded {len(tools_to_return)} tools from MCP server: {server_id}")
            return ToolCreationResult(
                tools=tools_to_return,
                requested_functions=requested_functions,
                found_functions=found_functions,
                missing_functions=missing_functions,
                error=None
            )
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_id}: {e}")
            return ToolCreationResult(
                tools=[],
                requested_functions=config.get("functions", []),
                found_functions=[],
                missing_functions=config.get("functions", []),
                error=str(e)
            )


class MCPHTTPAdapter(ToolAdapter):
    """Adapter for creating MCP tools from an HTTP endpoint."""
    def create(self, config: Dict[str, Any]) -> ToolCreationResult:
        server_id = config.get("id", "unknown-http-server")
        url = config.get("url")
        logger.debug(f"Connecting to MCP server '{server_id}' via HTTP at {url}")
        
        client_factory = lambda: streamablehttp_client(url)
        
        try:
            client = self.exit_stack.enter_context(MCPClient(client_factory))
            all_tools = client.list_tools_sync()
            
            # Check if specific functions were requested
            requested_functions = config.get("functions", [])
            if requested_functions:
                # Filter tools to only include requested functions
                found_functions = []
                filtered_tools = []
                
                for requested_func in requested_functions:
                    found = False
                    for tool in all_tools:
                        if hasattr(tool, 'tool_spec') and tool.tool_spec.get('name') == requested_func:
                            filtered_tools.append(tool)
                            found_functions.append(requested_func)
                            found = True
                            break
                    if not found:
                        logger.warning(f"MCP server '{server_id}' does not provide requested function '{requested_func}'")
                
                missing_functions = [f for f in requested_functions if f not in found_functions]
                tools_to_return = filtered_tools
            else:
                # No specific functions requested, return all tools
                requested_functions = []
                found_functions = [tool.tool_spec.get('name', 'unnamed') for tool in all_tools if hasattr(tool, 'tool_spec')]
                missing_functions = []
                tools_to_return = all_tools
            
            logger.info(f"Successfully loaded {len(tools_to_return)} tools from MCP server: {server_id}")
            return ToolCreationResult(
                tools=tools_to_return,
                requested_functions=requested_functions,
                found_functions=found_functions,
                missing_functions=missing_functions,
                error=None
            )
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_id}: {e}")
            return ToolCreationResult(
                tools=[],
                requested_functions=config.get("functions", []),
                found_functions=[],
                missing_functions=config.get("functions", []),
                error=str(e)
            )


class PythonToolAdapter(ToolAdapter):
    """Adapter for creating tools from local or installed Python modules."""
    def create(self, config: Dict[str, Any]) -> ToolCreationResult:
        """Creates a tool or tools based on the provided configuration."""
        tool_id, module_path, package_path, func_names, src_file = (config.get(k) for k in ["id", "module_path", "package_path", "functions", "source_file"])
        if not all([tool_id, module_path, func_names, src_file]):
            logger.warning(f"Python tool config is missing required fields. Skipping.")
            return ToolCreationResult(
                tools=[],
                requested_functions=func_names or [],
                found_functions=[],
                missing_functions=func_names or [],
                error="Missing required configuration fields"
            )
        source_dir = os.path.dirname(os.path.abspath(src_file))
        try:
            loaded_tools = []
            found_functions = []
            missing_functions = []
            
            # Look for the specific function names requested in the config
            for func_spec in func_names:
                if not isinstance(func_spec, str):
                    logger.warning(f"Function spec '{func_spec}' is not a string in tool config '{tool_id}'. Skipping.")
                    missing_functions.append(str(func_spec))
                    continue
                obj = None
                try:
                    obj = _load_module_attribute(module_path, func_spec, package_path, source_dir)
                except (ImportError, AttributeError, FileNotFoundError) as e:
                    logger.warning(f"Error loading function '{func_spec}' from module '{module_path}' (package_path '{package_path}')): {e}")
                    missing_functions.append(func_spec)
                    continue
                    
                # Accept any callable object - removed tool_spec check as it's unreliable
                if callable(obj):
                    # Clean up the tool name to remove path prefixes
                    clean_function_name = func_spec.split('.')[-1]
                    
                    # If the object has a tool_spec, update it with clean name
                    if hasattr(obj, 'tool_spec') and isinstance(obj.tool_spec, dict):
                        if 'name' in obj.tool_spec:
                            original_name = obj.tool_spec['name']
                            obj.tool_spec['name'] = clean_function_name
                            logger.debug(f"Renamed tool from '{original_name}' to '{clean_function_name}'")
                    
                    loaded_tools.append(obj)
                    found_functions.append(func_spec)
                    logger.debug(f"Successfully loaded callable '{func_spec}' as '{clean_function_name}' from module '{module_path}'")
                else:
                    logger.warning(f"Object '{func_spec}' in module '{module_path}' is not callable. Skipping.")
                    missing_functions.append(func_spec)
            
            logger.info(f"Successfully loaded {len(loaded_tools)} tools from Python module: {tool_id}")
            return ToolCreationResult(
                tools=loaded_tools,
                requested_functions=func_names,
                found_functions=found_functions,
                missing_functions=missing_functions,
                error=None
            )
        except Exception as e:
            logger.error(f"Failed to extract tools from Python module '{tool_id}': {e}")
            return ToolCreationResult(
                tools=[],
                requested_functions=func_names,
                found_functions=[],
                missing_functions=func_names,
                error=str(e)
            )

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
