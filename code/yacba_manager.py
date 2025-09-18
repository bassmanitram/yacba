# yacba_manager.py
# Manages the lifecycle of the chatbot agent and its client connections.

import os
import sys
import json
import importlib.util
from typing import List, Dict, Any, Optional, Callable
from contextlib import ExitStack
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger

from strands import Agent
from strands.tools.mcp import MCPClient
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

from framework_adapters import FrameworkAdapter
from model_loader import StrandsModelLoader
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
    def __init__(self, model_string: str, system_prompt: str, tool_configs: List[Dict[str, Any]], startup_files_content: Optional[List[Dict[str, Any]]], headless: bool = False, model_config: Optional[Dict[str, Any]] = None, session_name: Optional[str] = None, emulate_system_prompt: bool = False):
        self.model_string = model_string
        self.system_prompt = system_prompt
        self.tool_configs = tool_configs
        self.startup_files_content = startup_files_content
        self.headless = headless
        self.model_config = model_config or {}
        self.session_name = session_name
        self.emulate_system_prompt = emulate_system_prompt
        self.session_filepath: Optional[str] = f"{session_name}.yacba-session.json" if session_name else None
        self.agent: Optional[Agent] = None
        self.loaded_tools: List[Any] = []
        self.framework_adapter: Optional[FrameworkAdapter] = None
        self._exit_stack = ExitStack()
        self._tool_setters = {
            "mcp": self._setup_single_mcp_client,
            "python": self._setup_single_python_tool,
        }
        logger.debug("ChatbotManager initialized.")

    def set_session_name(self, name: str):
        """Updates the session name and file path for the manager."""
        self.session_name = name
        self.session_filepath = f"{name}.yacba-session.json"

    def save_session(self):
        """Saves the current agent's message history to the session file."""
        if not self.session_filepath:
            # In interactive mode, this is not an error, just a no-op if no session is active.
            # Provide feedback in case the user tried to /save without a session name.
            if not self.headless:
                print("No session name set. Use --session-name <name> or /save <name> to start a session.", file=sys.stderr)
            return

        if not self.agent or not self.agent.messages:
            logger.debug("Session history is empty. Nothing to save.")
            return
        
        try:
            with open(self.session_filepath, 'w', encoding='utf-8') as f:
                json.dump(self.agent.messages, f, indent=2, ensure_ascii=False)
            print(f"Session saved to '{self.session_filepath}'.")
        except IOError as e:
            print(f"Error saving session to '{self.session_filepath}': {e}", file=sys.stderr)

    def clear_session(self):
        """Clears the agent's current message history."""
        if self.agent:
            self.agent.messages.clear()
            print("Conversation history has been cleared.")

    def _load_session_if_exists(self) -> List[Dict[str, Any]]:
        """Loads a session from a file if it exists, otherwise returns an empty list."""
        if self.session_filepath and os.path.exists(self.session_filepath):
            try:
                with open(self.session_filepath, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
                    logger.info(f"Loaded {len(messages)} messages from session: {self.session_filepath}")
                    return messages
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Could not load or parse session file '{self.session_filepath}': {e}")
        return []

    def _setup_single_mcp_client(self, config: Dict[str, Any]) -> List[Any]:
        """Initializes one MCP client and returns its tools."""
        server_id = config.get("id", "unknown-server")
        try:
            client_factory = _get_mcp_client_factory(config)
            if not client_factory: return []
            client = self._exit_stack.enter_context(MCPClient(client_factory))
            tools = client.list_tools_sync()
            logger.info(f"Successfully loaded {len(tools)} tools from MCP server: {server_id}")
            return tools
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_id}: {e}")
            return []

    def _setup_single_python_tool(self, config: Dict[str, Any]) -> List[Any]:
        """Loads tools from a specified Python module."""
        tool_id, module_path, func_names, src_file = (config.get(k) for k in ["id", "module_path", "functions", "source_file"])
        if not all([tool_id, module_path, func_names, src_file]):
            logger.warning(f"Python tool config is missing required fields. Skipping.")
            return []

        resolved_path = os.path.abspath(os.path.join(os.path.dirname(src_file), module_path))
        if not os.path.exists(resolved_path):
            logger.error(f"Python module for tool '{tool_id}' not found at: {resolved_path}")
            return []

        try:
            spec = importlib.util.spec_from_file_location(name=tool_id, location=resolved_path)
            if not spec or not spec.loader: raise ImportError("Could not create module spec.")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            loaded_tools = []
            for name in func_names:
                obj = getattr(module, name, None)
                if obj and hasattr(obj, 'tool_spec'):
                    loaded_tools.append(obj)
                else:
                    logger.warning(f"Object '{name}' in '{resolved_path}' is not a valid Strands tool. Skipping.")
            
            logger.info(f"Successfully loaded {len(loaded_tools)} tools from Python module: {tool_id}")
            return loaded_tools
        except Exception as e:
            logger.error(f"Failed to load Python module tool '{tool_id}': {e}")
            return []

    def _initialize_all_tools(self) -> List[Any]:
        """Uses a thread pool to initialize all configured tools in parallel."""
        all_tools = []
        with ThreadPoolExecutor() as executor:
            future_to_config = {}
            for config in self.tool_configs:
                tool_id, tool_type = config.get("id"), config.get("type")
                if config.get("disabled"):
                    logger.info(f"Tool '{tool_id}' is disabled. Skipping.")
                    continue
                
                setup_func = self._tool_setters.get(tool_type)
                if setup_func:
                    future = executor.submit(setup_func, config)
                    future_to_config[future] = config
                else:
                    logger.warning(f"Tool '{tool_id}' has unknown type '{tool_type}'. Skipping.")

            for future in as_completed(future_to_config):
                try:
                    all_tools.extend(future.result())
                except Exception as e:
                    tool_id = future_to_config[future].get("id")
                    logger.error(f"Exception initializing tool '{tool_id}': {e}")
        return all_tools

    def _setup_agent(self) -> Optional[Agent]:
        """Creates the Strands agent instance."""
        try:
            loader = StrandsModelLoader()
            model, self.framework_adapter = loader.create_model(self.model_string, self.model_config)
            if not model: return None

            initial_messages = self._load_session_if_exists()
            
            agent_args = self.framework_adapter.prepare_agent_args(
                system_prompt=self.system_prompt,
                messages=initial_messages,
                startup_files_content=self.startup_files_content,
                emulate_system_prompt=self.emulate_system_prompt
            )
            
            self.agent = Agent(
                model=model, 
                tools=self.loaded_tools, 
                callback_handler=SilentToolUseCallbackHandler(headless=self.headless),
                **agent_args
            )
            logger.info("Agent successfully created.")
            return self.agent
        except Exception as e:
            logger.error(f"Fatal error initializing the agent: {e}", exc_info=True)
            return None

    def __enter__(self):
        """Initializes tools and agent."""
        self.loaded_tools = self._initialize_all_tools()
        self.agent = self._setup_agent()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Saves session and shuts down resources."""
        if not self.headless: self.save_session()
        logger.info("Shutting down tool clients...")
        self._exit_stack.close()
        logger.info("Shutdown complete.")

