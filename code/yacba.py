"""
Main entry point for the YACBA Chatbot application.
Fully typed version using yacba_types.
"""

import sys
import os
import asyncio
from typing import NoReturn, List, Optional
from loguru import logger

# Import migrated components with proper typing
from cli import (
    run_headless_mode,
    chat_loop_async,
)
from adapters.cli.commands.registry import BackendCommandRegistry
from adapters.cli.completer import YacbaCompleter
from utils.startup_messages import print_startup_info, print_welcome_message
from utils.content_processing import files_to_content_blocks
from core import ChatbotManager, parse_config, YacbaConfig
from yacba_types import ExitCode, Message


def _check_and_clear_cache_early():
    """Check for --clear-cache flag early and clear cache before config parsing."""
    # Quick check for --clear-cache flag without full argument parsing
    if '--clear-cache' in sys.argv:
        from utils.performance_utils import fs_cache
        fs_cache.clear()
        logger.info("Performance cache cleared")


def _format_startup_message(files_to_upload: List[tuple[str, str]]) -> Optional[List[Message]]:
    """
    Processes startup files using a memory-efficient generator and formats them
    into a single multi-modal message for the agent.

    Args:
        files_to_upload: A list of tuples containing file paths and their mimetypes.

    Returns:
        A list containing a single user message with file content, or None if no files.
    """
    if not files_to_upload:
        return None

    # Lazily process all files using a generator and collect the content blocks
    content_blocks = files_to_content_blocks(files_to_upload, add_headers=True)

    # If any blocks were generated, construct the final message
    if content_blocks:
        # Prepend the introductory text
        intro_block = {"type": "text", "text": "The user has uploaded the following files for analysis:"}
        # Append the concluding text
        outro_block = {"type": "text", "text": "\nPlease acknowledge you have received these files and await my instructions."}

        final_content = [intro_block] + content_blocks + [outro_block]
        return [{"role": "user", "content": final_content}]

    return None

async def main_async() -> None:
    """
    Main async function to orchestrate the chatbot application.
    It parses config, sets up the manager, and runs the appropriate loop.

    Raises:
        SystemExit: On configuration errors or initialization failures
    """
    # Clear cache early if requested, before config parsing
    _check_and_clear_cache_early()

    # Parse configuration using migrated config parser
    config: YacbaConfig = parse_config()

    # Validate headless mode requirements
    if config.headless and not config.initial_message:
        logger.error("Headless mode requires an initial message via -i or stdin.")
        sys.exit(ExitCode.CONFIG_ERROR)

    # Print welcome message for interactive mode
    if not config.headless:
        print_welcome_message()

    # Process startup files after parsing config and before initializing the manager/engine
    # This is YACBA's responsibility: file processing and content preparation
    config.startup_files_content = _format_startup_message(
        [(upload["path"], upload["mimetype"]) for upload in config.files_to_upload]
    )

    logger.info("Starting up Chatbot Manager...")

    # Use the migrated ChatbotManager with proper error handling
    try:
        with ChatbotManager(config) as manager:
            if not manager.is_ready:
                logger.error("Failed to initialize the agent engine. Exiting.")
                sys.exit(ExitCode.INITIALIZATION_ERROR)

            # Enhanced startup information with tool loading details and conversation manager info
            print_startup_info(
                model_id=config.model_string,
                system_prompt=config.system_prompt,
                prompt_source=config.prompt_source,
                tool_system_status=manager.engine.tool_system_status,
                startup_files=[(upload["path"], upload["mimetype"]) for upload in config.files_to_upload],
                conversation_manager_info=manager.engine.conversation_manager_info,
                output_file=sys.stderr
            )

            if not config.headless and config.tool_configs:
                print("Tools initialized.")

            # Run in appropriate mode
            if config.headless:
                success: bool = await run_headless_mode(
                    manager.engine,
                    config.initial_message)
                if not success:
                    sys.exit(ExitCode.RUNTIME_ERROR)
            else:
                command_registry = BackendCommandRegistry(manager.engine)
                completer = YacbaCompleter(command_registry.list_commands())
                await chat_loop_async(
                    manager.engine,
                    command_registry,
                    completer,
                    config.initial_message)

    except Exception as e:
        logger.error(f"Fatal error in ChatbotManager: {e}")
        sys.exit(ExitCode.FATAL_ERROR)


def main() -> NoReturn:
    """
    Synchronous main entry point. Configures logging and runs the async application.

    This function never returns normally - it either completes successfully
    or exits with an error code.
    """
    log_level: str = os.environ.get("LOGURU_LEVEL", "INFO").upper()
    logger.remove()
    logger.add(sys.stderr, level=log_level)

    try:
        asyncio.run(main_async())
        # If we get here, the application completed successfully
        sys.exit(ExitCode.SUCCESS)
    except KeyboardInterrupt:
        print("\nExiting.", file=sys.stderr)
        sys.exit(ExitCode.INTERRUPTED)

if __name__ == "__main__":
    main()
