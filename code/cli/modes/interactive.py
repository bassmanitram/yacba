"""
Interactive chat mode for YACBA CLI.

Handles the main interactive conversation loop with full UI features.
"""

import asyncio
import sys
from typing import Optional

from loguru import logger
from prompt_toolkit.application import Application
from prompt_toolkit.input import create_input
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.output import DummyOutput

from cli.commands.registry import CommandRegistry
# Note: Removed ChatState import as requested
from yacba_types.backend import ChatBackend
from ..interface import create_prompt_session


class ChatInterface:
    """
    Manages the interactive chat session, including user input, command handling,
    and robust cancellation of long-running tasks.
    """

    def __init__(
        self,
        backend: ChatBackend,
        command_handler: Optional[CommandRegistry] = None,
    ):
        """
        Initializes the chat interface.

        Args:
            backend: The chat backend instance to handle messages.
            command_handler: Handler for meta-commands (e.g., /help, /exit).
        """
        self.backend = backend
        self.command_handler = command_handler or CommandRegistry()
        self.session = create_prompt_session()
        self.main_app = self.session.app

    async def run(self, initial_message: Optional[str] = None):
        """Starts and manages the main interactive chat loop."""
        if initial_message:
            print(f"You: {initial_message}")
            await self._handle_chat_with_cancellation(initial_message)
            print()

        while True:
            try:
                user_input = await self.session.prompt_async("You: ")
                if self._should_exit(user_input):
                    break
                if not user_input.strip():
                    continue
                if user_input.strip().startswith("/"):
                    await self.command_handler.handle_command(user_input.strip())
                    continue

                logger.debug(f"Calling backend.handle_input with User input: {user_input}")
                await self._handle_chat_with_cancellation(user_input)

            except (KeyboardInterrupt, EOFError):
                print()
                break
            except Exception as e:
                logger.error(f"Error in chat loop: {e}")
                print(f"An error occurred: {e}", file=sys.stderr)

    def _should_exit(self, user_input: str) -> bool:
        """Checks for exit commands."""
        return user_input.strip().lower() in ["/exit", "/quit", "exit", "quit"]

    async def _handle_chat_with_cancellation(self, user_input: str):
        """
        Handles a chat request with support for cancellation that is robust against
        backend task exceptions.
        """

        cancel_future = asyncio.Future()

        kb = KeyBindings()
        @kb.add("escape", "c")
        def _(event):
            if not cancel_future.done():
                cancel_future.set_result(None)
            event.app.exit()

        cancel_app = Application(
            key_bindings=kb, output=DummyOutput(), input=create_input()
        )

        engine_task = asyncio.create_task(self.backend.handle_input(user_input))
        listener_task = asyncio.create_task(cancel_app.run_async())
        print("Thinking... (Press Alt+C to cancel)")

        try:
            done, pending = await asyncio.wait(
                [engine_task, cancel_future],
                return_when=asyncio.FIRST_COMPLETED,
            )

            if cancel_future in done:
                print("\nOperation cancelled by user.")
                engine_task.cancel()
            else:
                success = engine_task.result()
                if not success:
                    print("Operation failed.")

        except Exception as e:
            print(f"\nAn error occurred in the backend task: {e}")
            if not engine_task.done():
                engine_task.cancel()

        finally:
            # --- GUARANTEED UNIFIED CLEANUP ---
            # 1. Gracefully tell the listener app to shut down.
            if not cancel_app.is_done:
                cancel_app.exit()

            # 2. Wait for the listener task to fully complete and release the terminal.
            await listener_task

            # 3. Restore the main application's control over the terminal.
            self.main_app.renderer.reset()
            self.main_app.invalidate()
            await asyncio.sleep(0)

# Wrapper function to start the interface
async def chat_loop_async(
    backend: ChatBackend,
    command_handler: Optional[CommandRegistry] = None,
    initial_message: Optional[str] = None
):
    """
    Initializes and runs the interactive chat interface.
    """
    interface = ChatInterface(backend, command_handler)
    await interface.run(initial_message)