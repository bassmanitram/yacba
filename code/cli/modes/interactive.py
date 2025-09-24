"""
Interactive chat mode for YACBA CLI.

Handles the main interactive conversation loop with full UI features.
"""

import sys
from typing import Optional

from loguru import logger

from cli.commands.registry import CommandRegistry
from utils.content_processing import parse_input_with_files
from yacba_types.backend import ChatBackend
from ..interface import create_prompt_session

async def chat_loop_async(
    backend: ChatBackend,
    command_handler: Optional[CommandRegistry] = CommandRegistry(),
    initial_message: Optional[str] = None):
    """
    Runs the main interactive conversation loop using prompt_toolkit.

    Args:
        backend: ChatBackend instance
        initial_message: Optional initial message to send
        max_files: Maximum number of files to process
    """
    session = create_prompt_session()

    # Process initial message if provided
    if initial_message:
        print(f"You: {initial_message}")
        await backend.handle_input(user_input)
        print()

    # Main interaction loop
    while True:
        try:
            user_input = await session.prompt_async("You: ")

            # Handle exit commands
            if user_input.strip().lower() in ["/exit", "/quit", "exit", "quit"]:
                break

            # Skip empty input
            if not user_input.strip():
                continue

            # Handle meta-commands
            if user_input.strip().startswith("/"):
                await command_handler.handle_command(user_input.strip())
                continue

            # Process regular chat input
            logger.debug(f"Calling backend.handle_input with User input: {user_input}")
            await backend.handle_input(user_input)

        except (KeyboardInterrupt, EOFError):
            print()
            break
        except Exception as e:
            logger.error(f"Error in chat loop: {e}")
            print(f"An error occurred: {e}", file=sys.stderr)