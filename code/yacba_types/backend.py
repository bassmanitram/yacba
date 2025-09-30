from typing import Protocol
from typing import Protocol


class ChatBackend(Protocol):

    def startup(self):
        """
        Startup any necessary resources for the backend.
        """
        ...

    def shutdown(self):
        """
        Clean up any resources held by the backend.
        """
        ...
    async def handle_input(self, user_input: str, cancellation: bool = False):
        """
        Process user input and yield response chunks asynchronously.
        Allows for cancellation of the operation.

        Args:
            user_input: The input string from the user.
        """
        ...
    @property
    def is_ready(self) -> bool:
        """Check if the engine is ready for use."""
        ...
