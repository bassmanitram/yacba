"""
Custom callback handler for the Strands agent to control output verbosity.
Updated to support configurable tool use reporting and environment-controlled trace logging.
"""

import os
from typing import Any
from loguru import logger
from strands.handlers.callback_handler import PrintingCallbackHandler


class SilentToolUseCallbackHandler(PrintingCallbackHandler):
    """
    A callback handler that can optionally suppress tool use details for cleaner output.
    
    This handler allows configurable control over tool execution feedback:
    - When show_tool_use=False (default): Suppresses verbose tool execution details
    - When show_tool_use=True: Shows full tool execution feedback
    
    It is also responsible for:
    - Printing the "Chatbot: " prefix in interactive mode.
    - Printing the final newline after a response in interactive mode.
    
    Trace logging can be controlled via environment variables:
    - YACBA_TRACE_CUSTOM_HANDLER=1: Enable trace logging for this module only
    - YACBA_TRACE_LEVEL=TRACE: Set global trace level
    """

    def __init__(self, headless: bool = False, show_tool_use: bool = False):
        """
        Initialize the callback handler.
        
        Args:
            headless: Whether running in headless mode (no interactive prompts)
            show_tool_use: Whether to show verbose tool execution feedback
        """
        super().__init__()
        self.headless = headless
        self.show_tool_use = show_tool_use
        
        # Check if trace logging is enabled for this module via environment variable
        self.trace_enabled = (
            os.getenv('YACBA_TRACE_CUSTOM_HANDLER', '').lower() in ('1', 'true', 'yes', 'on') or
            os.getenv('YACBA_TRACE_LEVEL', '').upper() == 'TRACE'
        )

    def __call__(self, **kwargs: Any) -> None:
        """
        Intercepts feedback events from the agent to control terminal output.
        
        Args:
            **kwargs: Event data from the agent
        """
        # Conditional trace logging based on environment variable
        if self.trace_enabled:
            logger.trace("SilentToolUseCallbackHandler.__call__ arguments: {}", kwargs)
        
        event = kwargs.get("event", {})

        # In interactive mode, handle the "Chatbot:" prefix and final newline.
        if not self.headless:
            message_start = event.get("messageStart")
            if message_start and message_start.get("role") == "assistant":
                # Use a standard print for compatibility and simplicity.
                print("Chatbot: ", end="")

            if "messageStop" in event:
                print()  # Print the final newline.

        # Conditionally suppress tool usage information based on show_tool_use setting
        # If show_tool_use is False (default), suppress the tool use details
        # This removes the verbose "Using tool..." messages for cleaner output
        if not self.show_tool_use:
            kwargs.pop("current_tool_use", None)
        
        # Pass the remaining arguments (like messageChunk) to the parent handler,
        # which prints the actual content from the language model.
        super().__call__(**kwargs)
