"""
Interactive chat mode for YACBA CLI.

Handles the main interactive conversation loop with full UI features.
"""

import asyncio
from pathlib import Path
import sys
from typing import Optional

from loguru import logger
from prompt_toolkit import HTML, PromptSession, print_formatted_text as print
from prompt_toolkit.application import Application
from prompt_toolkit.input import create_input
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.completion import Completer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.history import FileHistory


from cli.commands.registry import CommandRegistry
from yacba_types.backend import AsyncREPLBackend

THINKING = HTML("<i><grey>Thinking... (Press Alt+C to cancel)</grey></i>")

class AsyncREPL:
    """
    Manages the interactive chat session, including user input, command handling,
    and robust cancellation of long-running tasks.
    """

    def __init__(
        self,
        backend: AsyncREPLBackend,
        command_handler: Optional[CommandRegistry] = None,
        completer: Optional[Completer] = None,
        prompt_string: Optional[str] = None,
        history_path: Optional[Path] = None
    ):
        """
        Initialize the asynchronous REPL interface.

        Args:
            backend (AsyncREPLBackend): The backend responsible for executing REPL commands asynchronously.
            command_handler (Optional[CommandRegistry], optional): Registry for handling custom commands. Defaults to a new CommandRegistry instance if not provided.
            completer (Optional[Completer], optional): Optional tab-completion logic for the REPL input.
            prompt_string (Optional[str], optional): Custom prompt string to display. Defaults to "User: " if not provided.
            history_path (Optional[Path], optional): Optional path to a file for storing command history.

        Attributes:
            backend (AsyncREPLBackend): The REPL backend.
            command_handler (CommandRegistry): The command handler registry.
            prompt_string (HTML): The prompt string, formatted as HTML.
            session (PromptSession): The prompt_toolkit session for user interaction.
            main_app: The main application instance from the prompt session.
        """
        self.backend = backend
        self.command_handler = command_handler or CommandRegistry()
        self.prompt_string = HTML(prompt_string or "User: ")

        self.session = PromptSession(
            history=self._create_history(history_path),
            key_bindings=self._create_key_bindings(),
            multiline=True,
            completer=completer,
        )
        self.main_app = self.session.app

    def _create_history(self, path: Path) -> FileHistory:
        """
        Creates and returns a FileHistory object for the given file path.
        If the provided path is not None, ensures that the parent directory exists
        by creating it if necessary, then returns a FileHistory instance associated
        with the specified path.
        Args:
            path (Path): The file path where the history should be stored.
        Returns:
            FileHistory: An instance of FileHistory for the specified path.
        """

        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            return FileHistory(path)

    def _create_key_bindings(self) -> KeyBindings:
        """
        Create key bindings for the prompt session.

        Key Bindings:
        - Enter: Add new line (natural typing behavior)
        - Alt+Enter: Send message (works in all terminals)

        Returns:
            KeyBindings instance with configured shortcuts
        """
        bindings = KeyBindings()

        @bindings.add("enter")
        def _(event):
            """Handle Enter key - add new line."""
            event.app.current_buffer.insert_text("\n")

        @bindings.add(Keys.Escape, "enter")
        def _(event):
            """Handle Alt+Enter - send message."""
            event.app.current_buffer.validate_and_handle()

        return bindings
    
    async def run(self, initial_message: Optional[str] = None):
        """
        Runs the asynchronous REPL (Read-Eval-Print Loop) session.
        If an initial message is provided, it is processed before entering the main loop.
        The method continuously prompts the user for input, processes commands (starting with '/'),
        and handles regular input by passing it to the backend. The loop can be exited by specific
        user input or keyboard interrupts.
        Args:
            initial_message (Optional[str], optional): An optional message to process before starting the REPL loop.
        Exceptions:
            Handles KeyboardInterrupt and EOFError to exit the loop gracefully.
            Logs and prints any other exceptions that occur during the loop.
        """
        
        if initial_message:
            print(self.prompt_string, end = "")
            print(initial_message)
            await self._process_input(initial_message)
            print()

        while True:
            try:
                user_input = await self.session.prompt_async(self.prompt_string)
                if self._should_exit(user_input):
                    break
                if not user_input.strip():
                    continue
                if user_input.strip().startswith("/"):
                    await self.command_handler.handle_command(user_input.strip())
                    continue

                logger.debug(f"Calling backend.handle_input with User input: {user_input}")
                await self._process_input(user_input)

            except (KeyboardInterrupt, EOFError):
                print()
                break
            except Exception as e:
                logger.error(f"Error in chat loop: {e}")
                print(f"An error occurred: {e}", file=sys.stderr)

    def _should_exit(self, user_input: str) -> bool:
        """Checks for exit commands."""
        return user_input.strip().lower() in ["/exit", "/quit"]

    async def _process_input(self, user_input: str):
        """
        Asynchronously processes user input, allowing for cancellation via a key binding.
        This method starts two concurrent tasks:
          1. A backend task that handles the provided user input.
          2. A listener application that waits for a specific key binding (Escape + 'c') to cancel the operation.
        If the user triggers the cancellation key binding, the backend task is cancelled and a cancellation message is printed.
        If the backend task completes first, its result is checked for success, and a failure message is printed if necessary.
        Any exceptions raised during backend processing are caught and reported.
        Regardless of outcome, the method ensures proper cleanup:
          - The listener application is shut down.
          - The listener task is awaited to release terminal control.
          - The main application's renderer and state are reset.
        Args:
            user_input (str): The input string to be processed by the backend.
        Raises:
            Exception: Any exception raised by the backend task is caught and reported.
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

        backend_task = asyncio.create_task(self.backend.handle_input(user_input))
        listener_task = asyncio.create_task(cancel_app.run_async())
        print(THINKING)

        try:
            done, pending = await asyncio.wait(
                [backend_task, cancel_future],
                return_when=asyncio.FIRST_COMPLETED,
            )

            if cancel_future in done:
                print("\nOperation cancelled by user.")
                backend_task.cancel()
            else:
                success = backend_task.result()
                if not success:
                    print("Operation failed.")

        except Exception as e:
            print(f"\nAn error occurred in the backend task: {e}")
            if not backend_task.done():
                backend_task.cancel()

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
async def run_async_repl(
    backend: AsyncREPLBackend,
    command_handler: Optional[CommandRegistry] = None,
    completer: Optional[Completer] = None,
    initial_message: Optional[str] = None,
    prompt_string: Optional[str] = None,
    history_path: Optional[Path] = None,
):
    """
    Initializes and runs the REPL.
    """
    repl = AsyncREPL(backend, command_handler, completer, prompt_string, history_path)
    await repl.run(initial_message)
