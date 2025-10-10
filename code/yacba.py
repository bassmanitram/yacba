"""
New main entry point for YACBA using strands_agent_factory and repl_toolkit.

This refactored version separates concerns:
- YACBA: Configuration management and CLI argument parsing
- strands_agent_factory: Agent lifecycle and tool management  
- repl_toolkit: Interactive and headless user interfaces

All existing functionality is preserved while using specialized packages.
"""

import nest_asyncio
import asyncio
nest_asyncio.apply()

import sys
import os
from pathlib import Path
from typing import NoReturn, Optional
from loguru import logger

# Add paths for the new dependencies (temporary for development)
sys.path.insert(0, "/home/jbartle9/tmp/strands_agent_factory")
sys.path.insert(0, "/home/jbartle9/tmp/repl_toolkit")

# YACBA core functionality - configuration and startup
from core import parse_config, YacbaConfig
from utils.startup_messages import print_startup_info, print_welcome_message
from yacba_types import ExitCode

# strands_agent_factory integration
from strands_agent_factory import AgentFactory
from adapters.strands_factory import YacbaToStrandsConfigConverter, YacbaStrandsBackend

# repl_toolkit integration
from repl_toolkit import run_async_repl, run_headless_mode
from adapters.repl_toolkit import YacbaCommandAdapter

# Use YACBA's existing completer directly
from adapters.cli.completer import YacbaCompleter


def _check_and_clear_cache_early():
    """Check for --clear-cache flag early and clear cache before config parsing."""
    if '--clear-cache' in sys.argv:
        from utils.performance_utils import fs_cache
        fs_cache.clear()
        logger.info("Performance cache cleared")


async def main_async() -> None:
    """
    Main async function orchestrating the refactored YACBA application.
    
    This function:
    1. Parses YACBA configuration (preserves all existing CLI functionality)
    2. Converts to strands_agent_factory configuration
    3. Creates and initializes AgentFactory
    4. Creates backend adapter implementing repl_toolkit protocols
    5. Runs appropriate mode (interactive or headless) using repl_toolkit
    
    Raises:
        SystemExit: On configuration errors or initialization failures
    """
    # Clear cache early if requested
    _check_and_clear_cache_early()
    
    # Parse YACBA configuration - preserves all existing argument handling
    logger.info("Parsing YACBA configuration...")
    config: YacbaConfig = parse_config()
    
    # Print welcome message for interactive mode
    if not config.headless:
        print_welcome_message()
    
    # Convert YACBA config to strands_agent_factory config
    logger.info("Converting configuration for strands_agent_factory...")
    config_converter = YacbaToStrandsConfigConverter(config)
    strands_config = config_converter.convert()
    
    # Create and initialize AgentFactory
    logger.info("Initializing strands agent factory...")
    agent_factory = AgentFactory(strands_config)
    
    # Initialize the factory
    success = await agent_factory.initialize()
    if not success:
        logger.error("Failed to initialize agent factory")
        sys.exit(ExitCode.INITIALIZATION_ERROR)
    
    # Create the agent
    agent = agent_factory.create_agent()
    if not agent:
        logger.error("Failed to create agent")
        sys.exit(ExitCode.INITIALIZATION_ERROR)
    
    # Use agent as context manager for proper resource cleanup
    try:
        with agent as agent_proxy:
            # Create backend adapter
            backend = YacbaStrandsBackend(agent_proxy)
            
            if not backend.is_ready:
                logger.error("Backend adapter is not ready")
                sys.exit(ExitCode.INITIALIZATION_ERROR)
            
            # Print startup information using YACBA's existing functionality
            _print_startup_info(config, agent_proxy)
            
            # Run in appropriate mode
            if config.headless:
                await _run_headless_mode(backend, config)
            else:
                await _run_interactive_mode(backend, config)
                
    except Exception as e:
        logger.error(f"Fatal error in agent lifecycle: {e}")
        sys.exit(ExitCode.FATAL_ERROR)


def _print_startup_info(config: YacbaConfig, agent_proxy) -> None:
    """
    Print startup information using YACBA's existing functionality.
    
    Args:
        config: YACBA configuration
        agent_proxy: The agent proxy instance
    """
    try:
        # Extract tool information from agent proxy
        tool_names = getattr(agent_proxy, 'tool_names', [])
        tool_count = len(tool_names) if tool_names else 0
        
        # Create a simple tool system status for compatibility
        tool_system_status = {
            'total_tools': tool_count,
            'loaded_tools': tool_count,
            'failed_tools': 0
        }
        
        # Create conversation manager info
        conversation_manager_info = {
            'type': config.conversation_manager_type,
            'sliding_window_size': config.sliding_window_size if config.uses_sliding_window else None,
            'preserve_recent': config.preserve_recent_messages if config.uses_summarizing else None
        }
        
        # Use YACBA's existing startup info function
        print_startup_info(
            model_id=config.model_string,
            system_prompt=config.system_prompt,
            prompt_source=config.prompt_source,
            tool_system_status=tool_system_status,
            startup_files=[(upload["path"], upload["mimetype"]) for upload in config.files_to_upload],
            conversation_manager_info=conversation_manager_info,
            output_file=sys.stderr
        )
        
        if not config.headless and config.tool_configs:
            print("Tools initialized.")
            
    except Exception as e:
        logger.warning(f"Error printing startup info: {e}")


async def _run_headless_mode(backend: YacbaStrandsBackend, config: YacbaConfig) -> None:
    """
    Run in headless mode using repl_toolkit.
    
    Args:
        backend: The backend adapter
        config: YACBA configuration
    """
    logger.info("Starting headless mode...")
    
    success = await run_headless_mode(
        backend=backend,
        initial_message=config.initial_message
    )
    
    if not success:
        logger.error("Headless mode completed with errors")
        sys.exit(ExitCode.RUNTIME_ERROR)


async def _run_interactive_mode(backend: YacbaStrandsBackend, config: YacbaConfig) -> None:
    """
    Run in interactive mode using repl_toolkit.
    
    Args:
        backend: The backend adapter  
        config: YACBA configuration
    """
    logger.info("Starting interactive mode...")
    
    # Create command adapter
    command_adapter = YacbaCommandAdapter(backend)
    
    # Disable completer for now to avoid async issues - can be re-enabled later
    completer = None
    
    # Prepare history path
    history_path = None
    if config.has_session:
        sessions_dir = Path.home() / ".yacba" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        history_path = sessions_dir / f"{config.session_name}_history.txt"
    
    # Run the async REPL
    await run_async_repl(
        backend=backend,
        command_handler=command_adapter,
        completer=completer,  # Disabled for now
        initial_message=config.initial_message,
        prompt_string=config.cli_prompt or "User: ",
        history_path=history_path
    )


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