"""
Backend adapter implementing repl_toolkit protocols for strands_agent_factory.

This module provides the bridge between YACBA's strands_agent_factory Agent
and the repl_toolkit AsyncBackend protocol
"""

from typing import Optional

from utils.logging import get_logger, log_error

from strands_agent_factory.core.agent import AgentProxy
from strands_agent_factory import AgentFactoryConfig
from repl_toolkit import iter_content_parts
from repl_toolkit.ptypes import AsyncBackend
import base64

logger = get_logger(__name__)


class YacbaBackend(AsyncBackend):
    """
    Adapter that wraps a strands_agent_factory AgentProxy to implement
    both AsyncBackend protocol for repl_toolkit.
    
    This allows YACBA to use repl_toolkit's interactive and headless
    interfaces while leveraging strands_agent_factory for agent management.
    """
    
    def __init__(self, agent_proxy: AgentProxy, config: Optional[AgentFactoryConfig] = None):
        """
        Initialize the backend adapter.
        
        Args:
            agent_proxy: The strands_agent_factory AgentProxy instance
            config: The AgentFactoryConfig for status reporting
        """
        self.agent_proxy = agent_proxy
        self.config = config
        logger.debug("yacba_backend_initialized")
    
    async def handle_input(self, user_input: str, images = None) -> bool:
        """
        Handle user input by processing it through the agent.
        
        This method implements both AsyncBackend an protocols
        by providing a unified interface for processing user input.
        
        Args:
            user_input: The input string from the user
            images: Optional list of images associated with the input
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        if not user_input.strip():
            logger.debug("empty_input_received")
            return True
        
        logger.debug("processing_user_input", preview=user_input[:100])
        
        try:
            if images:
                user_input = ''.join(
                    f" image('{base64.b64encode(image.data).decode('ascii')}') " if image
                    else content
                    for content, image in iter_content_parts(user_input, images)
                    if image or content
                )
        
            success = await self.agent_proxy.send_message_to_agent(user_input,show_user_input=False)           
            if success:
                logger.debug("input_processed_successfully")
            else:
                logger.warning("input_processing_returned_false")
                
            return success
            
        except Exception as e:
            log_error(logger, "error_processing_input", error=str(e))
            return False
    
    def get_agent_proxy(self) -> AgentProxy:
        """
        Get the underlying AgentProxy instance.
        
        This allows access to agent-specific functionality when needed
        by YACBA's command system or other components.
        
        Returns:
            AgentProxy: The wrapped agent proxy instance
        """
        return self.agent_proxy
    
    @property
    def is_ready(self) -> bool:
        """
        Check if the backend is ready to process input.
        
        Returns:
            bool: True if ready, False otherwise
        """
        # AgentProxy should be ready if it was created successfully
        return self.agent_proxy is not None
    
    def clear_conversation(self) -> bool:
        """
        Clear the conversation history.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Access the underlying agent and clear messages using synchronous context manager
            self.agent_proxy.clear_messages()
            logger.debug("conversation_history_cleared")
            return True
        except Exception as e:
            logger.error("error_clearing_conversation", error=str(e))
            return False
    
    def get_tool_names(self) -> list[str]:
        """
        Get list of available tool names.
        
        Returns:
            list[str]: List of tool names
        """
        try:
            # Access tool_specs from AgentProxy - this should be available directly
            tool_specs = getattr(self.agent_proxy, 'tool_specs', [])
            if not tool_specs:
                return []
            
            # Extract tool names from tool specs
            tool_names = []
            for tool_spec in tool_specs:
                if hasattr(tool_spec, 'name'):
                    tool_names.append(tool_spec.name)
                elif isinstance(tool_spec, dict) and 'name' in tool_spec:
                    tool_names.append(tool_spec['name'])
                elif hasattr(tool_spec, 'function') and hasattr(tool_spec.function, 'name'):
                    tool_names.append(tool_spec.function.name)
                else:
                    # Fallback: convert to string and try to extract name
                    tool_names.append(str(tool_spec))
            
            return tool_names
        except Exception as e:
            logger.error("error_getting_tool_names", error=str(e))
            return []
    
    def get_conversation_stats(self) -> dict:
        """
        Get conversation statistics.
        
        Returns:
            dict: Statistics about the conversation
        """
        try:
            # Get tool count
            tool_names = self.get_tool_names()
            tool_count = len(tool_names)
            
            # Try to get message count through context manager
            message_count = 0
            try:
                with self.agent_proxy as agent:
                    messages = getattr(agent, 'messages', [])
                    message_count = len(messages)
            except Exception as e:
                logger.debug("could_not_access_messages_through_context", error=str(e))
                # Try alternative access methods
                try:
                    messages = getattr(self.agent_proxy, 'messages', [])
                    message_count = len(messages) if messages else 0
                except:
                    message_count = 0
            
            return {
                "message_count": message_count,
                "tool_count": tool_count
            }
        except Exception as e:
            logger.error("error_getting_conversation_stats", error=str(e))
            return {"message_count": 0, "tool_count": 0}
