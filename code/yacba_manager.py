# yacba_manager.py
# Manages the lifecycle of the chatbot agent and its client connections.

import os
import sys
import importlib.util
from typing import List, Dict, Any, Optional, Callable
from contextlib import ExitStack
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed

from strands import Agent
from strands.tools.mcp import MCPClient
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

from custom_handler import SilentToolUseCallbackHandler
from model_loader import StrandsModelLoader

def _get_mcp_client_factory(config: Dict[str, Any]) -> Optional[Callable[[], Any]]:
    """
    Determines the correct MCP client factory based on the config.
    """
    server_id = config.get("id", "unknown-server")
    if "url" in config:
        return lambda: streamablehttp_client(config["url"])
    if "command" in config:
        process_env = os.environ.copy()
        if 'env' in config:
            process_env.update(config['env'])
        params = StdioServerParameters(command=config["command"], args=config.get("args", []), env=process_env)
        return lambda: stdio_client(params)
    logger.error(f"MCP config for '{server_id}' is invalid.")
    return None

class ChatbotManager:
    """
    A context manager to handle the setup and teardown of the Strands Agent
    and any associated tool clients.
    """
    def __init__(self, model_id: str, system_prompt: str, tool_configs: List[Dict[str, Any]], startup_files_content: Optional[List[Dict[str, Any]]], headless: bool = False, model_config: Optional[Dict[str, Any]] = None):
        self.model_id = model_id
        self.system_prompt = system_prompt
        self.tool_configs = tool_configs
        self.startup_files_content = startup_files_content
        self.headless = headless
        self.model_config = model_config or {}
        self.agent: Optional[Agent] = None
        self._exit_stack = ExitStack()
        self._tool_setters = {
            "mcp": self._setup_single_mcp_client,
            "python": self._setup_single_python_tool,
        }
        logger.debug("ChatbotManager initialized.")

    def _setup_single_mcp_client(self, config: Dict[str, Any]) -> List[Any]:
        """
        Initializes one MCP client and returns its tools.
        """
        server_id = config.get("id", "unknown-server")
        try:
            client_factory = _get_mcp_client_factory(config)
            if not client_factory: return []
            client = self._exit_stack.enter_context(MCPClient(client_factory))
            tools = client.list_tools_sync()
            logger.info(f"Connected to MCP server: {server_id}, loaded {len(tools)} tools.")
            return tools
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_id}: {e}")
            return []

    def _setup_single_python_tool(self, config: Dict[str, Any]) -> List[Callable]:
        """
        Loads tools from a specified Python module.
        """
        tool_id, module_path, f_names = config.get("id"), config.get("module_path"), config.get("functions", [])
        if not all([tool_id, module_path, f_names]):
            logger.warning(f"Python tool config is missing required fields. Skipping.")
            return []

        config_dir = os.path.dirname(config.get("source_file", "."))
        resolved_path = os.path.abspath(os.path.join(config_dir, module_path))
        if not os.path.exists(resolved_path):
            logger.error(f"Python module for tool '{tool_id}' not found at: {resolved_path}")
            return []

        try:
            spec = importlib.util.spec_from_file_location(name=tool_id, location=resolved_path)
            if not spec or not spec.loader: raise ImportError("Could not create module spec.")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            loaded_tools = []
            for name in f_names:
                func = getattr(module, name, None)
                if func and hasattr(func, 'tool_spec'):
                    loaded_tools.append(func)
                else:
                    logger.warning(f"Function '{name}' in '{resolved_path}' is not a valid @tool. Skipping.")
            logger.info(f"Loaded {len(loaded_tools)} functions from Python module: {tool_id}")
            return loaded_tools
        except Exception as e:
            logger.error(f"Failed to load Python tool '{tool_id}' from {resolved_path}: {e}")
            return []

    def _initialize_all_tools(self) -> List[Any]:
        """
        Initializes all configured tools in parallel.
        """
        all_tools: List[Any] = []
        with ThreadPoolExecutor() as executor:
            future_to_config = {}
            for config in self.tool_configs:
                tool_id = config.get("id", "unknown-tool")
                if config.get("disabled", False):
                    logger.info(f"Tool '{tool_id}' is disabled. Skipping.")
                    continue
                
                setup_function = self._tool_setters.get(config.get("type"))
                if setup_function:
                    future = executor.submit(setup_function, config)
                    future_to_config[future] = config
                else:
                    logger.warning(f"Tool '{tool_id}' has an unknown type. Skipping.")

            for future in as_completed(future_to_config):
                try: all_tools.extend(future.result())
                except Exception as e:
                    server_id = future_to_config[future].get("id", "unknown-server")
                    logger.error(f"Exception initializing tool {server_id}: {e}")
        return all_tools

    def _setup_agent(self, tools: List[Any]) -> Optional[Agent]:
        """
        Creates the Strands agent instance.
        """
        try:
            loader = StrandsModelLoader()
            model = loader.create_model(self.model_id, self.model_config)
            if not model:
                return None
            
            handler = SilentToolUseCallbackHandler(headless=self.headless)
            agent = Agent(
                model=model, tools=tools, system_prompt=self.system_prompt,
                callback_handler=handler, messages=self.startup_files_content)
            logger.info("Agent successfully created.")
            return agent
        except Exception as e:
            logger.error(f"Error initializing the agent: {e}")
            return None

    def __enter__(self):
        tools = self._initialize_all_tools()
        self.agent = self._setup_agent(tools=tools)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info("Shutting down tool clients...")
        self._exit_stack.close()
        logger.info("Shutdown complete.")
