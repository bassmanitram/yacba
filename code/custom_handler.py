# custom_handler.py
# Contains a custom callback handler to manage agent output.

from strands.handlers.callback_handler import PrintingCallbackHandler
from typing import Any

class SilentToolUseCallbackHandler(PrintingCallbackHandler):
    """
    A callback handler that intelligently formats agent output for both
    interactive and headless modes. It is responsible for:
    - Printing the "Chatbot: " prefix in interactive mode.
    - Printing the final newline after a response in interactive mode.
    - Suppressing the verbose 'current_tool_use' feedback from the agent.
    """
    def __init__(self, headless: bool = False, **kwargs: Any):
        super().__init__(**kwargs)
        self.headless = headless

    def __call__(self, **kwargs: Any) -> None:
        """
        Intercepts feedback events from the agent to control terminal output.
        """
        event = kwargs.get("event", {})

        # In interactive mode, handle the "Chatbot:" prefix and final newline.
        if not self.headless:
            message_start = event.get("messageStart")
            if message_start and message_start.get("role") == "assistant":
                # Use a standard print for compatibility and simplicity.
                print("Chatbot: ", end="")

            if "messageStop" in event:
                print() # Print the final newline.

        # Suppress the default printing of tool usage information in all modes.
        kwargs.pop("current_tool_use", None)
        
        # Pass the remaining arguments (like messageChunk) to the parent handler,
        # which prints the actual content from the language model.
        super().__call__(**kwargs)


