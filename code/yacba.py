#!/usr/bin/env python3
"""
YACBA - Yet Another ChatBot Agent

A flexible chatbot system that integrates with strands-agents for AI conversation
and tool usage, with support for multiple model providers and conversation management.
"""

import asyncio
import sys
from pathlib import Path
from typing import NoReturn

# Configure logging early
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


def _check_and_clear_cache_early():
    """Check for --clear-cache flag early and clear cache before config parsing."""
    if '--clear-cache' in sys.argv:
        logger.info("Cache clearing requested but no performance cache is active")


async def _run_agent_lifecycle(config: YacbaConfig) -> None:
    """
    Main agent lifecycle: configure, create agent, and run interface.
    
    Args:
        config: Validated YACBA configuration
        
    Raises:
        Exception: Any error during agent lifecycle
    """
    try:
        # Convert YACBA config to strands-agents format
        config_converter = YacbaToStrandsConfigConverter(config)
        strands_config = config_converter.convert()
        
        # Create agent factory and initialize it
        factory = AgentFactory(config=strands_config)
        await factory.initialize()  # Initialize the factory first
        
        # Create the agent
        agent = factory.create_agent()  # This should be synchronous after initialization
        
        # Create backend adapter
        backend = YacbaStrandsBackend(agent)
        
        # Create agent proxy for startup info
        class AgentProxy:
            def __init__(self, agent_instance):
                self.agent = agent_instance
                
            def get_available_tools(self):
                """Get list of available tool names."""
                try:
                    return self.agent.tool_names if hasattr(self.agent, 'tool_names') else []
                except Exception:
                    return []
                    
        agent_proxy = AgentProxy(agent)
        
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
    Print startup information using YACBA's existing startup message system.
    
    Args:
        config: YACBA configuration
        agent_proxy: Agent proxy for tool information
    """
    try:
        # Get basic info
        model_id = config.model_string or "Unknown"
        system_prompt = config.system_prompt or "No system prompt"
        prompt_source = config.prompt_source or "configuration"
        
        # Create dummy tool system status for compatibility
        from yacba_types.tools import ToolSystemStatus, ToolProcessingResult
        from yacba_types.config import ToolDiscoveryResult
        
        # Create minimal status objects
        discovery_result = ToolDiscoveryResult(
            successful_configs=[],
            failed_configs=[],
            total_files_scanned=0
        )
        
        tool_status = ToolSystemStatus(
            discovery_result=discovery_result,
            processing_results=[],
            total_tools_loaded=len(agent_proxy.get_available_tools())
        )
        
        # Get startup files (empty for now)
        startup_files = []
        
        # Use YACBA's existing startup message function
        print_startup_info(
            model_id=model_id,
            system_prompt=system_prompt,
            prompt_source=prompt_source,
            tool_system_status=tool_status,
            startup_files=startup_files,
            conversation_manager_info=f"Conversation Manager: {config.conversation_manager_type}"
        )
            
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
    
    # Disable completer for now to avoid async issues - can be re-enabled later
    completer = None
    
    # Prepare history path
    history_path = None
    if config.has_session:
        sessions_dir = Path.home() / ".yacba" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        history_path = sessions_dir / f"{config.session_name}_history.txt"
    
    # Run the async REPL without command handler (let repl_toolkit handle basic commands)
    await run_async_repl(
        backend=backend,
        command_handler=None,  # No custom command handler needed
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
    try:
        # Check for cache clearing before any imports that might use cache
        _check_and_clear_cache_early()
        
        print_welcome_message()
        
        # Parse configuration
        config = parse_config()
        
        # Run the main application
        asyncio.run(_run_agent_lifecycle(config))
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(ExitCode.USER_INTERRUPT)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(ExitCode.FATAL_ERROR)


if __name__ == "__main__":
    main()