# yacba_manager.py
# Manages the lifecycle of the chatbot agent and its MCP client connections.

import os
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
    and any associated MCP (Model Context Protocol) clients.
    """
    def __init__(self, model_id: str, system_prompt: str, mcp_configs: List[Dict[str, Any]], startup_files_content: Optional[List[Dict[str, Any]]], headless: bool = False):
        self.model_id = model_id
        self.system_prompt = system_prompt
        self.mcp_configs = mcp_configs
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
        if config.get("disabled", False):
            logger.info(f"MCP server '{server_id}' is disabled. Skipping.")
            return []

        try:
            client_factory = _get_mcp_client_factory(config)
            if not client_factory:
                return []

            # The ExitStack manages the client's __enter__ and __exit__ methods.
            client = self._exit_stack.enter_context(MCPClient(client_factory))
            tools = client.list_tools_sync()
            logger.info(f"Successfully connected to MCP server: {server_id}, loaded {len(tools)} tools.")
            return tools

        except Exception as e:
            logger.error(f"Failed to connect to or start MCP server {server_id}: {e}")
            return []

    def _initialize_all_tools(self) -> List[Any]:
        """
        Uses a thread pool to initialize all configured MCP clients in parallel.
        """
        all_tools = []
        with ThreadPoolExecutor() as executor:
            future_to_config = {executor.submit(self._setup_single_mcp_client, config): config for config in self.mcp_configs}
            for future in as_completed(future_to_config):
                try:
                    all_tools.extend(future.result())
                except Exception as e:
                    server_id = future_to_config[future].get("id", "unknown-server")
                    logger.error(f"Exception in thread for MCP server {server_id}: {e}")
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
        logger.info("Shutting down MCP clients...")
        self._exit_stack.close()
        logger.info("Shutdown complete.")


