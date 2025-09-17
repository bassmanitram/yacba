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

    if args.headless and not args.initial_message:
        logger.error("Headless mode requires an initial message from the -i option or from stdin.")
        sys.exit(1)

    tool_configs = discover_tool_configs(args.tools_dir)

    if not args.headless:
        print_welcome_message()
        if tool_configs:
            print("Attempting to initialize tools... this may take a moment.")

    startup_files_content = process_startup_files(args.files)
    logger.info("Starting up Chatbot Manager...")
    
    with ChatbotManager(
        model_id=args.model,
        system_prompt=args.system_prompt,
        tool_configs=tool_configs,
        startup_files_content=startup_files_content,
        headless=args.headless,
        model_config=args.model_config
    ) as manager:
        if not manager.agent:
            logger.error("Failed to initialize the agent. Exiting.")
            sys.exit(1)

        print_startup_info(
            model_id=args.model,
            system_prompt=args.system_prompt,
            prompt_source=args.prompt_source,
            tool_configs=tool_configs,
            startup_files=args.files,
            output_file=sys.stderr
        )

        if args.headless:
            success = await run_headless_mode(manager.agent, args.initial_message)
            if not success:
                sys.exit(1)
        else:
            await chat_loop_async(manager.agent, args.initial_message)

def main():
    """ 
    Synchronous main entry point.
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
