"""
Custom callback handler for the Strands agent to control output verbosity.
Updated to support configurable tool use reporting and environment-controlled trace logging.
"""

import os
from typing import Any
from loguru import logger
from strands.handlers.callback_handler import PrintingCallbackHandler


class CustomCallbackHandler(PrintingCallbackHandler):
    """
    A callback handler that can optionally suppress tool use details for cleaner output.
    
    This handler allows configurable control over tool execution feedback:
    - When show_tool_use=False (default): Suppresses verbose tool execution details
    - When show_tool_use=True: Shows full tool execution feedback
    
    It is also responsible for:
    - Printing the "Chatbot: " prefix in interactive mode.
    - Printing the final newline after a response in interactive mode.
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
        self.in_message = False
        
        # Check if trace logging is enabled for this module via environment variable

    def __call__(self, **kwargs: Any) -> None:
        """
        Intercepts feedback events from the agent to control terminal output.
        
        Args:
            **kwargs: Event data from the agent
        """

        logger.trace("SilentToolUseCallbackHandler.__call__ arguments: {}", kwargs)
        
        event = kwargs.get("event", {})

        # In interactive mode, handle the "Chatbot:" prefix and final newline.
        if not self.headless:
            data = kwargs.get("data", "")
            if data and not self.in_message:
                # Use a standard print for compatibility and simplicity.
                self.in_message = True
                print("Chatbot: ", end="")

            if "messageStop" in event and self.in_message:
                self.in_message = False
                print()  # Print the final newline.

        # Conditionally suppress tool usage information based on show_tool_use setting
        # If show_tool_use is False (default), suppress the tool use details
        # This removes the verbose "Using tool..." messages for cleaner output
        if self.show_tool_use:
            current_tool_use = kwargs.get("current_tool_use", {})            
            if current_tool_use and current_tool_use.get("name"):
                tool_name = current_tool_use.get("name", "Unknown tool")
                tool_input = current_tool_use.get("input", "")
                if self.previous_tool_use != current_tool_use:
                    self.previous_tool_use = current_tool_use
                    self.tool_count += 1
                    print(f"\nTool #{self.tool_count}: {tool_name}: {tool_input}")

        kwargs.pop("current_tool_use", None)
        
        # Pass the remaining arguments (like messageChunk) to the parent handler,
        # which prints the actual content from the language model.
        super().__call__(**kwargs)
