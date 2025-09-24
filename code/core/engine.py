# engine.py
# Contains the core, reusable logic for the YACBA agent.

import os
from typing import List, Dict, Any, Optional, Tuple
from contextlib import ExitStack
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger

from strands import Agent
from strands.agent.conversation_manager import ConversationManager
# Import the base class for correct type hinting
from strands.session.session_manager import SessionManager
from .agent import YacbaAgent
from utils.content_processing import parse_input_with_files
from yacba_types.backend import ChatBackend
from yacba_types.models import FrameworkAdapter
from adapters.tools.factory import ToolFactory
from .callback_handler import YacbaCallbackHandler
from .session import DelegatingSession
from .model_loader import StrandsModelLoader
from .config import YacbaConfig
from .conversation_manager_factory import ConversationManagerFactory
from yacba_types.tools import ToolProcessingResult, ToolSystemStatus

class YacbaEngine(ChatBackend):
    """
    The core, UI-agnostic engine for YACBA. It manages the agent, tools,
    model, and conversation management, but has no knowledge of the command line or session files.
    """
    def __init__(self, config: YacbaConfig, initial_messages: Optional[List[Dict[str, Any]]] = None):
        self.config = config
        self.initial_messages = initial_messages or []
        self.agent: Optional[Agent] = None
        self.conversation_manager: Optional[ConversationManager] = None
        self.loaded_tools: List[Any] = []
        self.tool_system_status: Optional[ToolSystemStatus] = None
        self.framework_adapter: Optional[FrameworkAdapter] = None
        self._exit_stack = ExitStack()
        self._tool_factory = ToolFactory(self._exit_stack)
        self.session_manager = DelegatingSession(
            session_name=config.session_name,
        )
        logger.debug("YacbaEngine initialized with DelegatingSession.")

    def _initialize_all_tools(self) -> Tuple[List[Any], ToolSystemStatus]:
        """Initialize all tools and return consolidated status."""
        all_tools = []
        processing_results = []
        
        with ThreadPoolExecutor() as executor:
            future_to_config = {
                executor.submit(self._load_single_tool_config, config): config
                for config in self.config.tool_configs
                if not config.get("disabled")
            }

            for future in as_completed(future_to_config):
                config = future_to_config[future]
                try:
                    result = future.result()
                    processing_results.append(result)
                    if result.has_tools:
                        all_tools.extend(result.tools)
                        logger.info(f"✓ Loaded {len(result.tools)} tools from '{result.config_id}' ({result.source_file})")
                    else:
                        logger.warning(f"✗ No tools loaded from '{result.config_id}' ({result.source_file}): {result.error_message}")
                except Exception as e:
                    config_id = config.get("id", "unknown")
                    source_file = config.get("source_file", "unknown")
                    error_result = ToolProcessingResult(
                        config_id=config_id,
                        source_file=source_file,
                        success=False,
                        tools=[],
                        requested_functions=config.get("functions", []),
                        found_functions=[],
                        missing_functions=config.get("functions", []),
                        error_message=f"Unexpected error: {e}"
                    )
                    processing_results.append(error_result)
                    logger.error(f"✗ Exception loading '{config_id}' ({source_file}): {e}")
        
        # Create consolidated status
        tool_system_status = ToolSystemStatus(
            discovery_result=self.config.tool_discovery_result,
            processing_results=processing_results,
            total_tools_loaded=len(all_tools)
        )
        
        return all_tools, tool_system_status

    def _load_single_tool_config(self, config: Dict[str, Any]) -> ToolProcessingResult:
        """Load tools from a single configuration with unified result tracking."""
        config_id = config.get("id", "unknown")
        source_file = config.get("source_file", "unknown")
        
        try:
            creation_result = self._tool_factory.create_tools(config)
            return ToolProcessingResult(
                config_id=config_id,
                source_file=source_file,
                success=len(creation_result.tools) > 0,
                tools=creation_result.tools,
                requested_functions=creation_result.requested_functions,
                found_functions=creation_result.found_functions,
                missing_functions=creation_result.missing_functions,
                error_message=creation_result.error
            )
        except Exception as e:
            return ToolProcessingResult(
                config_id=config_id,
                source_file=source_file,
                success=False,
                tools=[],
                requested_functions=config.get("functions", []),
                found_functions=[],
                missing_functions=config.get("functions", []),
                error_message=str(e)
            )

    def _create_conversation_manager(self) -> ConversationManager:
        """Create and configure the conversation manager."""
        try:
            manager = ConversationManagerFactory.create_conversation_manager(self.config)
            
            # Log the conversation manager configuration
            manager_info = ConversationManagerFactory.get_manager_info(manager, self.config)
            logger.info(manager_info)
            
            return manager
        except Exception as e:
            logger.error(f"Failed to create conversation manager: {e}")
            logger.info("Falling back to null conversation manager")
            from strands.agent.conversation_manager import NullConversationManager
            return NullConversationManager()

    def _setup_agent(self) -> Optional[Agent]:
        """Creates the Strands agent instance."""
        try:
            loader = StrandsModelLoader()
            model, self.framework_adapter = loader.create_model(self.config.model_string, self.config.model_config)
            if not model: return None
            
            # Allow the adapter to make any necessary modifications to the tool schemas.
            self.loaded_tools = self.framework_adapter.adapt_tools(self.loaded_tools, self.config.model_string)

            # Create conversation manager
            self.conversation_manager = self._create_conversation_manager()

            agent_args = self.framework_adapter.prepare_agent_args(
                system_prompt=self.config.system_prompt,
                messages=self.initial_messages,
                startup_files_content=self.config.startup_files_content,
                emulate_system_prompt=self.config.emulate_system_prompt
            )
            
            self.agent = YacbaAgent(
                adapter=self.framework_adapter,
                agent_id=self.config.agent_id or "yacba_agent",
                model=model, 
                tools=self.loaded_tools, 
                callback_handler=YacbaCallbackHandler(headless=self.config.headless, show_tool_use=self.config.show_tool_use),
                session_manager=self.session_manager,
                conversation_manager=self.conversation_manager,  # Add conversation manager
                **agent_args
            )
            logger.info("Agent successfully created with conversation management.")
            return self.agent
        except Exception as e:
            logger.error(f"Fatal error initializing the agent: {e}", exc_info=True)
            return None

    def startup(self):
        """Initializes tools and agent. To be called by the context manager."""
        self.loaded_tools, self.tool_system_status = self._initialize_all_tools()
        self.agent = self._setup_agent()
        return self.agent is not None
    
    async def handle_input(self, user_input: str) -> Any:
        """Handles user input and returns the agent's response."""
        if not self.agent:
            raise RuntimeError("Agent is not initialized.")
        agent_input = parse_input_with_files(user_input, self.config.max_files)
        await self.agent.handle_agent_stream(agent_input)

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
    
    @property
    def conversation_manager_info(self) -> str:
        """Get information about the current conversation manager."""
        if self.conversation_manager:
            return ConversationManagerFactory.get_manager_info(self.conversation_manager, self.config)
        return "Conversation Management: Not initialized"