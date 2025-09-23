"""
Interactive chat mode for YACBA CLI.

Handles the main interactive conversation loop with full UI features.
"""

import sys
from typing import Optional

from loguru import logger

from yacba_types.backend import ChatBackend
from content_processor import parse_input_with_files
from ..interface import create_prompt_session
from ..commands import CommandHandler

async def chat_loop_async(
    backend: ChatBackend,
    initial_message: Optional[str] = None,
    max_files: int = 20,
):
    """
    Runs the main interactive conversation loop using prompt_toolkit.

    Args:
        backend: ChatBackend instance
        initial_message: Optional initial message to send
        max_files: Maximum number of files to process
    """
    session = create_prompt_session()
    command_handler = CommandHandler(backend)

    # Process initial message if provided
    if initial_message:
        print(f"You: {initial_message}")
        agent_input = parse_input_with_files(initial_message, max_files)
        async for chunk in backend.stream_response(agent_input):
            print(chunk, end="", flush=True)
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
                await command_handler.handle(user_input.strip())
                continue

            # Process regular chat input
            agent_input = parse_input_with_files(user_input, max_files)
            async for chunk in backend.stream_response(agent_input):
                print(chunk, end="", flush=True)
            print()

        except (KeyboardInterrupt, EOFError):
            print()
            break
        except Exception as e:
            logger.error(f"Error in chat loop: {e}")
            print(f"An error occurred: {e}", file=sys.stderr)