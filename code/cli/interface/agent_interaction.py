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
from yacba_types.models import FrameworkAdapter
from .error_handling import format_error


async def handle_agent_stream(
    agent: Agent,
    message: Union[str, List[Dict[str, Any]]],
    adapter: FrameworkAdapter,
) -> bool:
    """
    Drives the agent's streaming response and handles potential errors.
    
    This function sends messages to the agent and processes the streaming response.
    The actual output formatting (including "Chatbot: " prefix, tool use display,
    and final newlines) is handled by the CustomCallbackHandler that was configured
    when the agent was created.
    
    Args:
        agent: The agent instance (with CustomCallbackHandler configured)
        message: Message to send to the agent
        adapter: Framework adapter for error handling and content transformation
        
    Returns:
        True on success, False on failure
    """
    if not message:
        return True

    exceptions_to_catch = adapter.expected_exceptions if adapter else (Exception,)

    try:
        # Transform the message using the framework adapter
        transformed_message = adapter.transform_content(message)
        
        # Stream the response - the CustomCallbackHandler handles all output formatting
        async for _ in agent.stream_async(transformed_message):
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


def validate_agent_ready(agent: Agent) -> bool:
    """
    Validate that an agent is ready for interaction.
    
    Args:
        agent: Agent to validate
        
    Returns:
        True if agent is ready, False otherwise
    """
    if not agent:
        logger.error("Agent is None")
        return False
    
    # Could add more validation here if needed
    return True

async def send_message_to_agent(
    agent: Agent,
    message: Union[str, List[Dict[str, Any]]],
    adapter: FrameworkAdapter,
    show_user_input: bool = True
) -> bool:
    """
    Higher-level function to send a message to the agent with optional input display.
    
    Args:
        agent: The agent instance
        message: Message to send
        adapter: Framework adapter
        show_user_input: Whether to display the user input
        
    Returns:
        True on success, False on failure
    """
    if show_user_input and isinstance(message, str):
        print(f"You: {message}")
    
    return await handle_agent_stream(agent, message, adapter)
