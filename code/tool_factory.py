"""
Tool factory .
YACBA handles configuration, strands handles execution.
"""

import os
import importlib
import importlib.util
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from contextlib import ExitStack

from loguru import logger
from yacba_types.tools import Tool, ToolConfig, ToolLoadResult
from performance_utils import lazy_import_mcp, timed_operation, perf_monitor


class ToolAdapter(ABC):
    """
    Abstract base class for a tool adapter.
    YACBA's responsibility: Configure and connect to tools.
    Strands' responsibility: Execute tools and handle protocols.
    """
    def __init__(self, exit_stack: ExitStack):
        self.exit_stack = exit_stack

    @abstractmethod
    def create(self, config: ToolConfig) -> ToolLoadResult:
        """
        Creates tools based on the provided configuration.
        
        Args:
            config: Tool configuration
            
        Returns:
            ToolLoadResult with tools, errors, and config ID
        """
        pass


class MCPStdIOAdapter(ToolAdapter):
    """Adapter for creating MCP tools from a stdio command with lazy loading."""
    
    @timed_operation("mcp_stdio_tool_creation")
    def create(self, config: ToolConfig) -> ToolLoadResult:
        """
        Creates MCP tools via stdio connection with lazy imports.
        YACBA handles connection setup, strands handles tool execution.
        
        Args:
            config: MCP tool configuration with stdio details
            
        Returns:
            ToolLoadResult with loaded tools or errors
        """
        server_id = config.get("id", "unknown-stdio-server")
        command = config.get("command")
        
        if not command:
            error_msg = f"MCP stdio config '{server_id}' missing required 'command' field"
            logger.error(error_msg)
            perf_monitor.increment_counter("mcp_stdio_config_errors")
            return ToolLoadResult(
                tools=[],
                errors=[error_msg],
                config_id=server_id
            )
        
        logger.debug(f"Starting MCP server '{server_id}' with command: {command}")
        
        # Prepare environment
        process_env = os.environ.copy()
        if 'env' in config:
            process_env.update(config['env'])
        
        try:
            # Lazy import MCP dependencies
            mcp_libs = lazy_import_mcp()
            MCPClient = mcp_libs['MCPClient']
            StdioServerParameters = mcp_libs['StdioServerParameters']
            stdio_client = mcp_libs['stdio_client']
            
            # Create connection parameters
            params = StdioServerParameters(
                command=command, 
                args=config.get("args", []), 
                env=process_env
            )
            client_factory = lambda: stdio_client(params)
            
            # Let strands-mcp handle the actual connection and tool discovery
            client = self.exit_stack.enter_context(MCPClient(client_factory))
            tools = client.list_tools_sync()
            
            logger.info(f"Successfully loaded {len(tools)} tools from MCP server: {server_id}")
            perf_monitor.increment_counter("mcp_stdio_tools_loaded", len(tools))
            return ToolLoadResult(
                tools=tools,
                errors=[],
                config_id=server_id
            )
        except Exception as e:
            error_msg = f"Failed to connect to MCP server {server_id}: {e}"
            logger.error(error_msg)
            perf_monitor.increment_counter("mcp_stdio_connection_errors")
            return ToolLoadResult(
                tools=[],
                errors=[error_msg],
                config_id=server_id
            )


class MCPHTTPAdapter(ToolAdapter):
    """Adapter for creating MCP tools from an HTTP server with lazy loading."""
    
    @timed_operation("mcp_http_tool_creation")
    def create(self, config: ToolConfig) -> ToolLoadResult:
        """
        Creates MCP tools via HTTP connection with lazy imports.
        YACBA handles connection setup, strands handles tool execution.
        
        Args:
            config: MCP tool configuration with HTTP details
            
        Returns:
            ToolLoadResult with loaded tools or errors
        """
        server_id = config.get("id", "unknown-http-server")
        url = config.get("url")
        
        if not url:
            error_msg = f"MCP HTTP config '{server_id}' missing required 'url' field"
            logger.error(error_msg)
            perf_monitor.increment_counter("mcp_http_config_errors")
            return ToolLoadResult(
                tools=[],
                errors=[error_msg],
                config_id=server_id
            )
        
        logger.debug(f"Connecting to MCP HTTP server '{server_id}' at: {url}")
        
        try:
            # Lazy import MCP dependencies
            mcp_libs = lazy_import_mcp()
            MCPClient = mcp_libs['MCPClient']
            streamablehttp_client = mcp_libs['streamablehttp_client']
            
            # Create HTTP client factory
            client_factory = lambda: streamablehttp_client(url)
            
            # Let strands-mcp handle the actual connection and tool discovery
            client = self.exit_stack.enter_context(MCPClient(client_factory))
            tools = client.list_tools_sync()
            
            logger.info(f"Successfully loaded {len(tools)} tools from MCP HTTP server: {server_id}")
            perf_monitor.increment_counter("mcp_http_tools_loaded", len(tools))
            return ToolLoadResult(
                tools=tools,
                errors=[],
                config_id=server_id
            )
        except Exception as e:
            error_msg = f"Failed to connect to MCP HTTP server {server_id}: {e}"
            logger.error(error_msg)
            perf_monitor.increment_counter("mcp_http_connection_errors")
            return ToolLoadResult(
                tools=[],
                errors=[error_msg],
                config_id=server_id
            )


class PythonModuleAdapter(ToolAdapter):
    """Adapter for creating tools from Python modules with lazy loading."""
    
    @timed_operation("python_module_tool_creation")
    def create(self, config: ToolConfig) -> ToolLoadResult:
        """
        Creates tools from a Python module with lazy imports.
        YACBA handles module loading, strands handles tool execution.
        
        Args:
            config: Python module tool configuration
            
        Returns:
            ToolLoadResult with loaded tools or errors
        """
        module_id = config.get("id", "unknown-python-module")
        module_path = config.get("module")
        
        if not module_path:
            error_msg = f"Python module config '{module_id}' missing required 'module' field"
            logger.error(error_msg)
            perf_monitor.increment_counter("python_module_config_errors")
            return ToolLoadResult(
                tools=[],
                errors=[error_msg],
                config_id=module_id
            )
        
        logger.debug(f"Loading Python module '{module_id}' from: {module_path}")
        
        try:
            # Handle both file paths and module names
            if os.path.isfile(module_path):
                # Load from file path
                spec = importlib.util.spec_from_file_location(module_id, module_path)
                if spec is None or spec.loader is None:
                    raise ImportError(f"Could not load module spec from {module_path}")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                # Load from module name
                module = importlib.import_module(module_path)
            
            # Look for tools in the module
            tools = []
            if hasattr(module, 'get_tools'):
                # Module provides a get_tools function
                module_tools = module.get_tools()
                if isinstance(module_tools, list):
                    tools.extend(module_tools)
                else:
                    tools.append(module_tools)
            elif hasattr(module, 'tools'):
                # Module has a tools attribute
                if isinstance(module.tools, list):
                    tools.extend(module.tools)
                else:
                    tools.append(module.tools)
            else:
                # Look for tool-like objects in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if hasattr(attr, '__call__') and not attr_name.startswith('_'):
                        # This looks like a tool function
                        tools.append(attr)
            
            if not tools:
                logger.warning(f"No tools found in Python module '{module_id}'")
            
            logger.info(f"Successfully loaded {len(tools)} tools from Python module: {module_id}")
            perf_monitor.increment_counter("python_module_tools_loaded", len(tools))
            return ToolLoadResult(
                tools=tools,
                errors=[],
                config_id=module_id
            )
            
        except Exception as e:
            error_msg = f"Failed to load Python module {module_id}: {e}"
            logger.error(error_msg)
            perf_monitor.increment_counter("python_module_load_errors")
            return ToolLoadResult(
                tools=[],
                errors=[error_msg],
                config_id=module_id
            )


class ToolFactory:
    """
    Optimized factory for creating and managing different types of tools with performance monitoring.
    YACBA handles configuration and connection, strands handles execution.
    """
    
    def __init__(self, exit_stack: ExitStack):
        self.exit_stack = exit_stack
        self._adapters: Dict[str, ToolAdapter] = {}
        self._initialize_adapters()
    
    def _initialize_adapters(self):
        """Initialize tool adapters lazily."""
        # Adapters are created on-demand to avoid unnecessary imports
        pass
    
    def _get_adapter(self, tool_type: str) -> Optional[ToolAdapter]:
        """Get or create an adapter for the given tool type."""
        if tool_type not in self._adapters:
            if tool_type == "mcp-stdio":
                self._adapters[tool_type] = MCPStdIOAdapter(self.exit_stack)
            elif tool_type == "mcp-http":
                self._adapters[tool_type] = MCPHTTPAdapter(self.exit_stack)
            elif tool_type == "python-module":
                self._adapters[tool_type] = PythonModuleAdapter(self.exit_stack)
            else:
                logger.warning(f"Unknown tool type: {tool_type}")
                return None
        
        return self._adapters.get(tool_type)
    
    @timed_operation("tool_creation")
    def create_tools(self, config: ToolConfig) -> ToolLoadResult:
        """
        Creates tools based on the provided configuration with performance monitoring.
        
        Args:
            config: Tool configuration dictionary
            
        Returns:
            ToolLoadResult with tools, errors, and config ID
        """
        tool_type = config.get("type")
        tool_id = config.get("id", "unknown-tool")
        
        if not tool_type:
            error_msg = f"Tool config '{tool_id}' missing required 'type' field"
            logger.error(error_msg)
            perf_monitor.increment_counter("tool_creation_errors")
            return ToolLoadResult(
                tools=[],
                errors=[error_msg],
                config_id=tool_id
            )
        
        adapter = self._get_adapter(tool_type)
        if not adapter:
            error_msg = f"No adapter available for tool type '{tool_type}' in config '{tool_id}'"
            logger.error(error_msg)
            perf_monitor.increment_counter("tool_creation_errors")
            return ToolLoadResult(
                tools=[],
                errors=[error_msg],
                config_id=tool_id
            )
        
        perf_monitor.increment_counter("tool_creation_attempts")
        return adapter.create(config)


# Maintain backward compatibility
ToolFactory = ToolFactory
