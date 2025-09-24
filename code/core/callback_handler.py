"""
Custom callback handler for the Strands agent to control output verbosity.
Updated to support configurable tool use reporting and environment-controlled trace logging.
"""

import os
from typing import Any
from loguru import logger
from strands.handlers.callback_handler import PrintingCallbackHandler

# A sensible maximum length for tool input values
MAX_VALUE_LENGTH = 90

class YacbaCallbackHandler(PrintingCallbackHandler):
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
        self.in_tool_use = False
        # Check env var once at startup for efficiency
        self.disable_truncation = os.environ.get('YACBA_SHOW_FULL_TOOL_INPUT', 'false').lower() == 'true'

    def _format_and_print_tool_input(self, tool_name: str, tool_input: Any):
        """Formats and prints tool input, handling truncation."""
        print(f"\nTool #{self.tool_count}: {tool_name}")

        if not isinstance(tool_input, dict):
            # Handle non-dict input (e.g., strings, lists)
            value_str = str(tool_input)
            if not self.disable_truncation and len(value_str) > MAX_VALUE_LENGTH:
                value_str = value_str[:MAX_VALUE_LENGTH] + '...'
            print(f"  - input: {value_str}")
            return

        # Handle dictionary input
        for key, value in tool_input.items():
            value_str = str(value)
            # Apply truncation only if it's enabled and the string is too long
            if not self.disable_truncation and len(value_str) > MAX_VALUE_LENGTH:
                value_str = value_str[:MAX_VALUE_LENGTH] + '...'
            print(f"  - {key}: {value_str}")

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
            if current_tool_use:
                if not self.in_tool_use:
                    self.tool_count += 1
                    self.in_tool_use = True
                self.previous_tool_use = current_tool_use
            
            if "messageStop" in event and self.in_tool_use:
                if self.previous_tool_use:
                    self._format_and_print_tool_input(
                        tool_name=self.previous_tool_use.get("name", "Unknown tool"),
                        tool_input=self.previous_tool_use.get("input", {})
                    )
                    self.previous_tool_use = None
                self.in_tool_use = False

        kwargs.pop("current_tool_use", None)
        
        # Pass the remaining arguments (like messageChunk) to the parent handler,
        # which prints the actual content from the language model.
        super().__call__(**kwargs)
