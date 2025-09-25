"""
Agent interaction utilities for YACBA CLI.

Handles the core logic for communicating with agents and processing responses.
The actual output formatting and display is handled by the CustomCallbackHandler
that's configured when the agent is created.
"""

import sys
from typing import Union, List, Dict, Any

from loguru import logger
from strands import Agent
from cli.interface.error_handling import format_error
from yacba_types.models import FrameworkAdapter

class YacbaAgent(Agent):
    """
    A subclass of Agent that could include additional YACBA-specific functionality.
    Currently, it behaves the same as the base Agent class.
    """

    def __init__(self, adapter: FrameworkAdapter, **kwargs: Any) -> None:
        """
        Initialize YacbaAgent with framework adapter.
        
        Args:
            adapter: Framework adapter for this agent
            **kwargs: All other arguments passed to parent Agent constructor
        """
        # Store adapter before calling parent constructor
        self.adapter = adapter
        
        # Call parent constructor with all other arguments
        super().__init__(**kwargs)

    async def handle_agent_stream(self,
        message: Union[str, List[Dict[str, Any]]]) -> bool:
        """
        Drives the agent's streaming response and handles potential errors.
        
        This function sends messages to the agent and processes the streaming response.
        The actual output formatting (including "Chatbot: " prefix, tool use display,
        and final newlines) is handled by the CustomCallbackHandler that was configured
        when the agent was created.
        
        Args:
            message: Message to send to the agent
            
        Returns:
            True on success, False on failure
        """
        if not message:
            return True

        exceptions_to_catch = self.adapter.expected_exceptions

        try:
            # Transform the message using the framework adapter
            transformed_message = self.adapter.transform_content(message)
            
            # Stream the response - the CustomCallbackHandler handles all output formatting
            async for _ in self.stream_async(transformed_message):
                pass
                
            return True
        except exceptions_to_catch as e:
            error_details = format_error(e)
            print(
                f"\nA model provider error occurred:\n{error_details}", file=sys.stderr
            )
            return False
        except Exception as e:
            logger.error(f"Unexpected error in agent stream: {e}")
            print(
                f"\nAn unexpected error occurred while generating the response: {e}",
                file=sys.stderr,
            )
            return False


    async def send_message_to_agent(self,
        message: Union[str, List[Dict[str, Any]]],
        show_user_input: bool = True
    ) -> bool:
        """
        Higher-level function to send a message to the agent with optional input display.
        
        Args:
            message: Message to send
            show_user_input: Whether to display the user input
            
        Returns:
            True on success, False on failure
        """
        if show_user_input and isinstance(message, str):
            print(f"You: {message}")
        
        return await self.handle_agent_stream(message)