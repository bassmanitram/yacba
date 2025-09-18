# yacba.py
# Main entry point for the YACBA Chatbot application.

import sys
import os
import asyncio
from loguru import logger

from yacba_manager import ChatbotManager
from cli_handler import print_welcome_message, print_startup_info, chat_loop_async, run_headless_mode
from content_processor import process_startup_files
from config_parser import parse_config

async def main_async():
    """
    Main async function to orchestrate the chatbot application.
    It parses config, sets up the manager, and runs the appropriate loop.
    """
    config = parse_config()

    if config.headless and not config.initial_message:
        logger.error("Headless mode requires an initial message via -i or stdin.")
        sys.exit(1)

    if not config.headless:
        print_welcome_message()

    # Process startup files after parsing config and before initializing the manager/engine
    config.startup_files_content = process_startup_files(config.files_to_upload, config.max_files)

    logger.info("Starting up Chatbot Manager...")
    
    with ChatbotManager(config) as manager:
        if not manager.engine or not manager.engine.agent:
            logger.error("Failed to initialize the agent engine. Exiting.")
            sys.exit(1)

        print_startup_info(
            model_id=config.model_string,
            system_prompt=config.system_prompt,
            prompt_source=config.prompt_source,
            loaded_tools=manager.engine.loaded_tools,
            startup_files=config.files_to_upload,
            output_file=sys.stderr
        )
        if not config.headless and config.tool_configs:
            print("Tools initialized.")

        if config.headless:
            success = await run_headless_mode(manager, config.initial_message)
            if not success:
                sys.exit(1)
        else:
            await chat_loop_async(manager, config.initial_message, config.max_files)

def main():
    """ 
    Synchronous main entry point. Configures logging and runs the async application.
    """
    log_level = os.environ.get("LOGURU_LEVEL", "INFO").upper()
    logger.remove()
    logger.add(sys.stderr, level=log_level)
    
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nExiting.", file=sys.stderr)
    except Exception as e:
        logger.error(f"An unhandled exception occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
