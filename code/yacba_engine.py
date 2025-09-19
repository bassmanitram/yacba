# yacba_engine.py
# Contains the core, reusable logic for the YACBA agent.

import os
from typing import List, Dict, Any, Optional
from contextlib import ExitStack
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger

from strands import Agent
from framework_adapters import FrameworkAdapter
from model_loader import StrandsModelLoader
from custom_handler import CustomCallbackHandler
from yacba_config import YacbaConfig
from tool_factory import ToolFactory


class YacbaEngine:
    """
    The core, UI-agnostic engine for YACBA. It manages the agent, tools,
    and model, but has no knowledge of the command line or session files.
    """
    def __init__(self, config: YacbaConfig, initial_messages: Optional[List[Dict[str, Any]]] = None):
        self.config = config
        self.initial_messages = initial_messages or []
        self.agent: Optional[Agent] = None
        self.loaded_tools: List[Any] = []
        self.framework_adapter: Optional[FrameworkAdapter] = None
        self._exit_stack = ExitStack()
        self._tool_factory = ToolFactory(self._exit_stack)
        logger.debug("YacbaEngine initialized.")

    def _initialize_all_tools(self) -> List[Any]:
        """Uses a thread pool to initialize all configured tools in parallel."""
        all_tools = []
        with ThreadPoolExecutor() as executor:
            future_to_config = {
                executor.submit(self._tool_factory.create_tools, config): config
                for config in self.config.tool_configs
                if not config.get("disabled")
            }

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
            model, self.framework_adapter = loader.create_model(self.config.model_string, self.config.model_config)
            if not model: return None
            
            # Allow the adapter to make any necessary modifications to the tool schemas.
            self.loaded_tools = self.framework_adapter.adapt_tools(self.loaded_tools, self.config.model_string)

            agent_args = self.framework_adapter.prepare_agent_args(
                system_prompt=self.config.system_prompt,
                messages=self.initial_messages,
                startup_files_content=self.config.startup_files_content,
                emulate_system_prompt=self.config.emulate_system_prompt
            )
            
            self.agent = Agent(
                model=model, 
                tools=self.loaded_tools, 
                callback_handler=CustomCallbackHandler(headless=self.config.headless, show_tool_use=self.config.show_tool_use),
                **agent_args
            )
            logger.info("Agent successfully created.")
            return self.agent
        except Exception as e:
            logger.error(f"Fatal error initializing the agent: {e}", exc_info=True)
            return None

    def startup(self):
        """Initializes tools and agent. To be called by the context manager."""
        self.loaded_tools = self._initialize_all_tools()
        self.agent = self._setup_agent()
        return self.agent is not None

    def shutdown(self):
        """Shuts down resources."""
        logger.info("Shutting down tool clients...")
        self._exit_stack.close()
        logger.info("Shutdown complete.")

    @property
    def is_ready(self) -> bool:
        """Check if the engine is ready for use."""
        return (
            self.agent is not None and 
            self.framework_adapter is not None
        )
