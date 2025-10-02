"""
Custom callback handler for the Strands agent to control output verbosity.
Updated to support configurable tool use reporting and environment-controlled trace logging.
"""

import os
from typing import Any, Optional
from loguru import logger
from prompt_toolkit import HTML, print_formatted_text
from strands.handlers.callback_handler import PrintingCallbackHandler

from utils.general_utils import print_structured_data

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

    def __init__(self, headless: Optional[bool] = False, 
        show_tool_use: Optional[bool] = False,
        response_prefix: Optional[str] = None
        ):
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
        self.response_prefix = HTML(response_prefix or "Chatbot: ")


    def _format_and_print_tool_input(self, tool_name: str, tool_input: Any):
        """Formats and prints tool input, handling truncation."""
        print_formatted_text(f"\nTool #{self.tool_count}: {tool_name}")
        print_structured_data(tool_input, 1, -1 if self.disable_truncation else MAX_VALUE_LENGTH, printer = print_formatted_text)

    def __call__(self, **kwargs: Any) -> None:
        """
        Intercepts feedback events from the agent to control terminal output.

        Args:
            **kwargs: Event data from the agent
        """

        logger.trace("SilentToolUseCallbackHandler.__call__ arguments: {}", kwargs)

        event = kwargs.get("event", {})
        reasoningText = kwargs.get("reasoningText", False)
        data = kwargs.get("data", "")
        complete = kwargs.get("complete", False)
        current_tool_use = kwargs.get("current_tool_use", {})

        # In interactive mode, handle the "Chatbot:" prefix and final newline.
        if not self.headless:
            if data and not self.in_message:
                self.in_message = True
                print_formatted_text(self.response_prefix, end = "", flush = True)

            if "messageStop" in event and self.in_message:
                self.in_message = False
                print_formatted_text(flush = True)  # Print the final newline.

        if reasoningText:
            print_formatted_text(reasoningText, end="")

        if data:
            print_formatted_text(data, end="" if not complete else "\n")

        # Conditionally suppress tool usage information based on show_tool_use setting
        # If show_tool_use is False (default), suppress the tool use details
        # This removes the verbose "Using tool..." messages for cleaner output
        if self.show_tool_use:
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

        if complete and data:
            print_formatted_text("\n")
