# yacba_manager.py
# Manages the lifecycle of the chatbot agent and its client connections.

import os
import sys
import importlib.util
from typing import List, Dict, Any, Optional, Callable
from contextlib import ExitStack
import litellm
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed

from strands import Agent
from strands.models.litellm import LiteLLMModel
from strands.tools.mcp import MCPClient
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

from custom_handler import SilentToolUseCallbackHandler

def _get_mcp_client_factory(config: Dict[str, Any]) -> Optional[Callable[[], Any]]:
    """
    Determines the correct MCP client factory (stdio or http) based on the config.
    Returns a callable factory function or None if the config is invalid.
    """
    server_id = config.get("id", "unknown-server")
    if "url" in config:
        logger.debug(f"Connecting to MCP server '{server_id}' via HTTP at {config['url']}")
        return lambda: streamablehttp_client(config["url"])
    
    if "command" in config:
        logger.debug(f"Starting MCP server '{server_id}' with command: {config['command']}")
        process_env = os.environ.copy()
        if 'env' in config:
            process_env.update(config['env'])
        params = StdioServerParameters(command=config["command"], args=config.get("args", []), env=process_env)
        return lambda: stdio_client(params)
        
    logger.error(f"MCP config for '{server_id}' is missing 'url' or 'command'. Cannot connect.")
    return None

class ChatbotManager:
    """
    A context manager to handle the setup and teardown of the Strands Agent
    and any associated tool clients.
    """
    def __init__(self, model_id: str, system_prompt: str, tool_configs: List[Dict[str, Any]], startup_files_content: Optional[List[Dict[str, Any]]], headless: bool = False):
        self.model_id = model_id
        self.system_prompt = system_prompt
        self.tool_configs = tool_configs
        self.startup_files_content = startup_files_content
        self.headless = headless
        self.agent: Optional[Agent] = None
        self._exit_stack = ExitStack()
        logger.debug("ChatbotManager initialized.")

    def _setup_single_mcp_client(self, config: Dict[str, Any]) -> List[Any]:
        """
        Initializes one MCP client, connects to its server, and returns its tools.
        """
        server_id = config.get("id", "unknown-server")
        try:
            client_factory = _get_mcp_client_factory(config)
            if not client_factory:
                return []

            client = self._exit_stack.enter_context(MCPClient(client_factory))
            tools = client.list_tools_sync()
            logger.info(f"Successfully connected to MCP server: {server_id}, loaded {len(tools)} tools.")
            return tools

        except Exception as e:
            logger.error(f"Failed to connect to or start MCP server {server_id}: {e}")
            return []

    def _setup_single_python_tool(self, config: Dict[str, Any]) -> List[Callable]:
        """
        Loads tools from a specified Python module.
        """
        tool_id = config.get("id", "unknown-tool")
        module_path = config.get("module_path")
        function_names = config.get("functions", [])
        config_source_file = config.get("source_file", ".")

        if not module_path or not function_names:
            logger.warning(f"Python tool '{tool_id}' is missing 'module_path' or 'functions'. Skipping.")
            return []

        # Resolve the module_path relative to the directory of the .tools.json file.
        config_dir = os.path.dirname(config_source_file)
        resolved_path = os.path.abspath(os.path.join(config_dir, module_path))

        if not os.path.exists(resolved_path):
            logger.error(f"Python module for tool '{tool_id}' not found at resolved path: {resolved_path}")
            return []

        try:
            # Create a module spec from the file path
            spec = importlib.util.spec_from_file_location(name=tool_id, location=resolved_path)
            if not spec or not spec.loader:
                raise ImportError(f"Could not create module spec for {resolved_path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            loaded_tools = []
            for func_name in function_names:
                if hasattr(module, func_name):
                    loaded_tools.append(getattr(module, func_name))
                else:
                    logger.warning(f"Function '{func_name}' not found in module at '{resolved_path}'.")
            
            logger.info(f"Successfully loaded {len(loaded_tools)} functions from Python module: {tool_id}")
            return loaded_tools

        except Exception as e:
            logger.error(f"Failed to load Python module tool '{tool_id}' from {resolved_path}: {e}")
            return []

    def _initialize_all_tools(self) -> List[Any]:
        """
        Uses a thread pool to initialize all configured tools in parallel.
        """
        all_tools: List[Any] = []
        
        with ThreadPoolExecutor() as executor:
            future_to_config = {}
            for config in self.tool_configs:
                tool_id = config.get("id", "unknown-tool")

                if config.get("disabled", False):
                    logger.info(f"Tool '{tool_id}' is disabled. Skipping.")
                    continue

                tool_type = config.get("type")
                if tool_type == "mcp":
                    future = executor.submit(self._setup_single_mcp_client, config)
                    future_to_config[future] = config
                elif tool_type == "python":
                    future = executor.submit(self._setup_single_python_tool, config)
                    future_to_config[future] = config
                else:
                    logger.warning(f"Tool '{tool_id}' has an unknown type: '{tool_type}'. Skipping.")

            for future in as_completed(future_to_config):
                try:
                    all_tools.extend(future.result())
                except Exception as e:
                    server_id = future_to_config[future].get("id", "unknown-server")
                    logger.error(f"Exception in thread for tool {server_id}: {e}")
        return all_tools

    def _setup_agent(self, tools: List[Any]) -> Optional[Agent]:
        """
        Validates the environment and creates the Strands agent instance.
        """
        try:
            logger.info(f"Validating environment for model: {self.model_id}...")
            litellm.validate_environment(model=self.model_id)
            
            model = LiteLLMModel(model_id=self.model_id)
            handler = SilentToolUseCallbackHandler(headless=self.headless)
            
            agent = Agent(
                model=model, 
                tools=tools, 
                system_prompt=self.system_prompt,
                callback_handler=handler,
                messages=self.startup_files_content
            )
            logger.info("Agent successfully created.")
            return agent
        except Exception as e:
            logger.error(f"Error initializing the agent: {e}")
            return None

    def __enter__(self):
        """Initializes tools and the agent when entering the 'with' block."""
        tools = self._initialize_all_tools()
        self.agent = self._setup_agent(tools=tools)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Shuts down all resources when exiting the 'with' block."""
        logger.info("Shutting down tool clients...")
        self._exit_stack.close()
        logger.info("Shutdown complete.")