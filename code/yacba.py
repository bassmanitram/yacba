# yacba.py
# Main entry point for the LiteLLM Chatbot application.

import sys
import os
import asyncio
from loguru import logger

from yacba_manager import ChatbotManager
from cli_handler import print_welcome_message, print_startup_info, chat_loop_async, run_headless_mode
from utils import discover_tool_configs
from content_processor import process_startup_files
from config_parser import parse_arguments

async def main_async():
    """
    Main async function to orchestrate the chatbot application.
    It parses arguments, sets up the manager, and runs the appropriate loop.
    """
    args = parse_arguments()

    # In headless mode, an initial message is required to do anything.
    if args.headless and not args.initial_message:
        logger.error("Headless mode requires an initial message from the -i option or from stdin.")
        sys.exit(1)

    # Discover tool configurations early to display the warning message promptly.
    tool_configs = discover_tool_configs(args.tools_dir)

    # In interactive mode, print welcome messages before the potentially slow tool initialization.
    if not args.headless:
        print_welcome_message()
        if tool_configs:
            print("Attempting to initialize tools... this may take a moment.")

    # Process any files provided at startup.
    startup_files_content = process_startup_files(args.files)

    logger.info("Starting up Chatbot Manager...")
    
    # Use the ChatbotManager to handle the lifecycle of the agent and its tools.
    # The slow initialization happens when this 'with' block is entered.
    with ChatbotManager(
        model_id=args.model,
        system_prompt=args.system_prompt,
        tool_configs=tool_configs,
        startup_files_content=startup_files_content,
        headless=args.headless
    ) as manager:
        if not manager.agent:
            logger.error("Failed to initialize the agent. Exiting.")
            sys.exit(1)

        # Print a summary of the configuration to stderr for logging purposes.
        print_startup_info(
            model_id=args.model,
            system_prompt=args.system_prompt,
            prompt_source=args.prompt_source,
            tool_configs=tool_configs,
            startup_files=args.files,
            output_file=sys.stderr
        )

        # Run the appropriate mode based on the --headless flag.
        if args.headless:
            await run_headless_mode(manager.agent, args.initial_message)
        else:
            await chat_loop_async(manager.agent, args.initial_message)

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
        logger.error(f"An unhandled exception occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()