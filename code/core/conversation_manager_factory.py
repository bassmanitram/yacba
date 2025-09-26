"""
Factory for creating conversation managers based on configuration.

This module provides a centralized way to create and configure conversation managers
for the YACBA agent, supporting different strategies for managing conversation history.
"""

from typing import Optional
from loguru import logger

from strands.agent.conversation_manager import (
    ConversationManager,
    NullConversationManager,
    SlidingWindowConversationManager,
    SummarizingConversationManager
)
from strands import Agent

from .config import YacbaConfig
from .model_loader import StrandsModelLoader


class ConversationManagerFactory:
    """Factory for creating conversation managers based on YACBA configuration."""
    
    @staticmethod
    def create_conversation_manager(config: YacbaConfig) -> ConversationManager:
        """
        Create a conversation manager based on the configuration.
        
        Args:
            config: YACBA configuration containing conversation manager settings
            
        Returns:
            Configured conversation manager instance
            
        Raises:
            ValueError: If configuration is invalid
            Exception: If manager creation fails
        """
        try:
            if config.conversation_manager_type == "null":
                logger.debug("Creating NullConversationManager")
                return NullConversationManager()
            
            elif config.conversation_manager_type == "sliding_window":
                logger.debug(f"Creating SlidingWindowConversationManager with window_size={config.sliding_window_size}")
                return SlidingWindowConversationManager(
                    window_size=config.sliding_window_size,
                    should_truncate_results=config.should_truncate_results
                )
            
            elif config.conversation_manager_type == "summarizing":
                logger.debug(f"Creating SummarizingConversationManager with summary_ratio={config.summary_ratio}")
                
                # Create optional summarization agent if a different model is specified
                summarization_agent = None
                if config.summarization_model:
                    logger.debug(f"Creating summarization agent with model: {config.summarization_model}")
                    try:
                        summarization_agent = ConversationManagerFactory._create_summarization_agent(
                            config.summarization_model
                        )
                        if summarization_agent:
                            logger.info(f"Successfully created summarization agent")
                        else:
                            logger.warning(f"Failed to create summarization agent, proceeding without one")
                    except Exception as e:
                        logger.error(f"Error creating summarization agent: {e}")
                        logger.info("Proceeding without summarization agent")
                        summarization_agent = None
                
                # Create the summarizing conversation manager
                logger.debug("Creating SummarizingConversationManager instance")
                return SummarizingConversationManager(
                    summary_ratio=config.summary_ratio,
                    preserve_recent_messages=config.preserve_recent_messages,
                    summarization_agent=summarization_agent,
                    summarization_system_prompt=config.custom_summarization_prompt
                )
            
            else:
                raise ValueError(f"Unknown conversation manager type: {config.conversation_manager_type}")
                
        except Exception as e:
            logger.error(f"Failed to create conversation manager: {e}")
            logger.debug("Exception details:", exc_info=True)
            logger.info("Falling back to NullConversationManager")
            return NullConversationManager()
    
    @staticmethod
    def _create_summarization_agent(model_string: str) -> Optional[Agent]:
        """
        Create a separate agent for summarization using a different model.
        
        Args:
            model_string: Model string for the summarization agent
            
        Returns:
            Configured agent for summarization, or None if creation fails
        """
        try:
            logger.debug(f"Loading summarization model: {model_string}")
            
            loader = StrandsModelLoader()
            
            # FIXED: Don't pass base_model_config - let the model use its own defaults
            # This avoids configuration conflicts between different model types
            model, adapter = loader.create_model(model_string, adhoc_config={})
            
            if not model:
                logger.warning(f"Failed to create summarization model: {model_string}")
                return None
            
            logger.debug("Summarization model loaded successfully")
            
            # Create agent args for summarization agent
            agent_args = adapter.prepare_agent_args(
                system_prompt="You are a conversation summarizer.",
                messages=[],
                startup_files_content=None,
                emulate_system_prompt=False
            )
            
            logger.debug("Creating summarization agent with lightweight configuration")
            
            # Import here to avoid circular dependency
            from .callback_handler import YacbaCallbackHandler
            
            # Create a lightweight agent for summarization (no tools, simple callback)
            summarization_agent = Agent(
                model=model,
                tools=[],  # No tools for summarization
                callback_handler=YacbaCallbackHandler(headless=True, show_tool_use=False),
                conversation_manager=None,  # No conversation management for summarization agent
                agent_id="yacba_summarization_agent",
                **agent_args
            )
            
            logger.info(f"Successfully created summarization agent with model: {model_string}")
            return summarization_agent
            
        except Exception as e:
            logger.error(f"Failed to create summarization agent: {e}")
            logger.debug("Summarization agent creation exception:", exc_info=True)
            return None
    
    @staticmethod
    def get_manager_info(manager: ConversationManager, config: YacbaConfig) -> str:
        """
        Get human-readable information about the conversation manager.
        
        Args:
            manager: The conversation manager instance
            config: YACBA configuration
            
        Returns:
            String describing the conversation manager configuration
        """
        if isinstance(manager, NullConversationManager):
            return "Conversation Management: Disabled (full history preserved)"
        
        elif isinstance(manager, SlidingWindowConversationManager):
            truncate_info = "with result truncation" if config.should_truncate_results else "without result truncation"
            return f"Conversation Management: Sliding Window (size: {config.sliding_window_size}, {truncate_info})"
        
        elif isinstance(manager, SummarizingConversationManager):
            summary_info = f"ratio: {config.summary_ratio}, preserve: {config.preserve_recent_messages}"
            model_info = f", model: {config.summarization_model}" if config.summarization_model else ""
            return f"Conversation Management: Summarizing ({summary_info}{model_info})"
        
        else:
            return f"Conversation Management: {type(manager).__name__}"