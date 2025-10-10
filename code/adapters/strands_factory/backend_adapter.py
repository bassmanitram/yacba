"""
Backend adapter implementing repl_toolkit protocols for strands_agent_factory.

This module provides the bridge between YACBA's strands_agent_factory Agent
and the repl_toolkit AsyncBackend/HeadlessBackend protocols.
"""

from typing import Optional
from loguru import logger

from strands_agent_factory.core.agent import AgentProxy
from repl_toolkit.ptypes import AsyncBackend, HeadlessBackend


class YacbaStrandsBackend(AsyncBackend, HeadlessBackend):
    """
    Adapter that wraps a strands_agent_factory AgentProxy to implement
    both AsyncBackend and HeadlessBackend protocols for repl_toolkit.
    
    This allows YACBA to use repl_toolkit's interactive and headless
    interfaces while leveraging strands_agent_factory for agent management.
    """
    
    def __init__(self, agent_proxy: AgentProxy):
        """
        Initialize the backend adapter.
        
        Args:
            agent_proxy: The strands_agent_factory AgentProxy instance
        """
        self.agent_proxy = agent_proxy
        logger.debug("Initialized YacbaStrandsBackend with AgentProxy")
    
    async def handle_input(self, user_input: str) -> bool:
        """
        Handle user input by processing it through the agent.
        
        This method implements both AsyncBackend and HeadlessBackend protocols
        by providing a unified interface for processing user input.
        
        Args:
            user_input: The input string from the user
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        if not user_input.strip():
            logger.debug("Received empty input, ignoring")
            return True
        
        logger.debug(f"Processing user input: {user_input[:100]}{'...' if len(user_input) > 100 else ''}")
        
        try:
            # Use the AgentProxy's send_message_to_agent method
            # This handles all the strands-agents complexity internally
            success = await self.agent_proxy.send_message_to_agent(user_input)
            
            if success:
                logger.debug("Input processed successfully")
            else:
                logger.warning("Input processing returned False")
                
            return success
            
        except Exception as e:
            logger.error(f"Error processing input: {e}")
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
    
    async def clear_conversation(self) -> bool:
        """
        Clear the conversation history.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Access the underlying agent and clear messages
            self.agent_proxy.clear_messages()
            logger.debug("Conversation history cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
            return False
    
    def get_tool_names(self) -> list[str]:
        """
        Get list of available tool names.
        
        Returns:
            list[str]: List of tool names
        """
        try:
            return getattr(self.agent_proxy, 'tool_names', [])
        except Exception as e:
            logger.error(f"Error getting tool names: {e}")
            return []
    
    async def get_conversation_stats(self) -> dict:
        """
        Get conversation statistics.
        
        Returns:
            dict: Statistics about the conversation
        """
        try:
            # This will depend on what statistics the agent proxy provides
            # For now, return basic info
            return {
                "message_count": len(getattr(self.agent_proxy, 'messages', [])),
                "tool_count": len(self.get_tool_names())
            }
        except Exception as e:
            logger.error(f"Error getting conversation stats: {e}")
            return {}