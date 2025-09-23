"""
Error handling and formatting for YACBA CLI.

Provides consistent error formatting and agent interaction error handling.
"""

import sys
from typing import Union, List, Dict, Any

from loguru import logger
from strands import Agent
from yacba_types.models import FrameworkAdapter


def format_error(e: Exception) -> str:
    """
    Extracts detailed information from exceptions for better user feedback.
    
    Args:
        e: Exception to format
        
    Returns:
        Formatted error message with details
    """
    details = f"Error Type: {type(e).__name__}"
    message = getattr(e, "message", None)
    if message:
        details += f"\nMessage: {message}"
    
    response = getattr(e, "response", None)
    if response and hasattr(response, "text"):
        details += f"\nOriginal Response: {response.text}"
        
    return str(e)


async def handle_agent_stream(
    agent: Agent,
    message: Union[str, List[Dict[str, Any]]],
    adapter: FrameworkAdapter,
) -> bool:
    """
    Drives the agent's streaming response and handles potential errors.
    
    Args:
        agent: The agent instance
        message: Message to send to the agent
        adapter: Framework adapter for error handling
        
    Returns:
        True on success, False on failure
    """
    if not message:
        return True

    exceptions_to_catch = adapter.expected_exceptions if adapter else (Exception,)

    try:
        transformed_message = adapter.transform_content(message)
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
