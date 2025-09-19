"""
Main entry point for the YACBA Chatbot application.
Fully typed version using yacba_types.
"""

import sys
import os
import asyncio
from typing import NoReturn
from loguru import logger

# Import migrated components with proper typing
from yacba_manager import ChatbotManager
from cli_handler import print_welcome_message, print_startup_info, chat_loop_async, run_headless_mode
from content_processor import process_startup_files
from config_parser import parse_config
from yacba_config import YacbaConfig
from yacba_types.base import ExitCode


async def main_async() -> None:
    """
    Main async function to orchestrate the chatbot application.
    It parses config, sets up the manager, and runs the appropriate loop.
    
    Raises:
        SystemExit: On configuration errors or initialization failures
    """
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
    config.startup_files_content = process_startup_files(
        [(upload["path"], upload["mimetype"]) for upload in config.files_to_upload], 
        config.max_files
    )

    logger.info("Starting up Chatbot Manager...")
    
    # Use the migrated ChatbotManager with proper error handling
    try:
        with ChatbotManager(config) as manager:
            if not manager.is_ready:
                logger.error("Failed to initialize the agent engine. Exiting.")
                sys.exit(ExitCode.INITIALIZATION_ERROR)

            # Print startup information
            print_startup_info(
                model_id=config.model_string,
                system_prompt=config.system_prompt,
                prompt_source=config.prompt_source,
                loaded_tools=manager.engine.loaded_tools if manager.engine else [],
                startup_files=[(upload["path"], upload["mimetype"]) for upload in config.files_to_upload],
                output_file=sys.stderr
            )
            
            if not config.headless and config.tool_configs:
                print("Tools initialized.")

            # Run in appropriate mode
            if config.headless:
                success: bool = await run_headless_mode(manager, config.initial_message)
                if not success:
                    sys.exit(ExitCode.RUNTIME_ERROR)
            else:
                await chat_loop_async(manager, config.initial_message, config.max_files)
                
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
    except Exception as e:
        logger.error(f"An unhandled exception occurred: {e}", exc_info=True)
        sys.exit(ExitCode.FATAL_ERROR)


if __name__ == "__main__":
    main()
