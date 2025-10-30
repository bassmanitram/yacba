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

# YACBA core functionality - configuration and startup
from adapters.repl_toolkit.completer import YacbaCompleter
from config import parse_config, YacbaConfig
from utils.startup_messages import print_startup_info, print_welcome_message
from yacba_types import ExitCode

# strands_agent_factory integration
from strands_agent_factory import AgentFactory
from strands_agent_factory.core.agent import AgentProxy
from adapters.strands_factory import YacbaToStrandsConfigConverter

# repl_toolkit integration
from repl_toolkit import AsyncREPL, HeadlessREPL
from adapters.repl_toolkit import YacbaBackend, YacbaActionRegistry


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
        
        # Create action registry with backend
        action_registry = YacbaActionRegistry()
        
        # Run in appropriate mode
        if config.headless:
            await _run_headless_mode(agent, action_registry, config, strands_config)
        else:
            await _run_interactive_mode(agent, action_registry, config, strands_config)
                
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
        
        # Use YACBA's existing startup message function
        print_startup_info(
            model_id=model_id,
            system_prompt=system_prompt,
            prompt_source=prompt_source,
            tools=agent_proxy.tool_specs or [],
            startup_files=config.files_to_upload or [],
            conversation_manager_info=f"Conversation Manager: {config.conversation_manager_type}"
        )
            
    except Exception as e:
        logger.error(f"Error printing startup info: {e}")


async def _run_headless_mode(agent: AgentProxy, action_registry: YacbaActionRegistry, config: YacbaConfig, strands_config) -> None:
    """
    Run in headless mode using repl_toolkit.
    
    Args:
        agent: The agent proxy
        action_registry: The action registry
        config: YACBA configuration
        strands_config: Converted strands_agent_factory configuration
    """
    logger.info("Starting headless mode...")

    repl = HeadlessREPL(        
        action_registry=action_registry,
    )

    success = False
    with agent as agent_context:
        # Create backend adapter
        backend = YacbaBackend(agent_context, strands_config)
       
        # Run the async REPL
        success = await repl.run(
            backend=backend,
            initial_message="Evaluate" if agent.has_initial_messages else None,
        )

    if not success:
        logger.error("Headless mode completed with errors")
        sys.exit(ExitCode.RUNTIME_ERROR)


async def _run_interactive_mode(agent: AgentProxy, action_registry: YacbaActionRegistry, config: YacbaConfig, strands_config) -> None:
    """
    Run in interactive mode using repl_toolkit.
    
    Args:
        agent: The agent proxy
        action_registry: The action registry
        config: YACBA configuration
        strands_config: Converted strands_agent_factory configuration
    """
    logger.info("Starting interactive mode...")
    
    # Create the custom completer
    completer = YacbaCompleter(meta_commands=action_registry.list_commands())
    
    # Prepare history path
    if config.session_name:
        sessions_dir = Path.home() / ".yacba" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        history_path = sessions_dir / f"{config.session_name}_history.txt"
    else:
        history_path = Path.home() / ".yacba/history.txt"  # No session, no history file
    
    repl = AsyncREPL(        
        action_registry=action_registry,
        completer=completer,
        prompt_string=config.cli_prompt or "User: ",
        history_path=history_path,
        enable_system_prompt=True,
        enable_suspend=True
    )

    with agent as agent_context:
        # Create backend adapter
        backend = YacbaBackend(agent_context, strands_config)

        # Print startup information
        _print_startup_info(config, agent_context)
        
        # Run the async REPL
        await repl.run(
            backend=backend,
            initial_message="Evaluate" if agent.has_initial_messages else None,
        )

def main() -> NoReturn:
    """
    Synchronous main entry point. Configures logging and runs the async application.
    
    This function never returns normally - it either completes successfully
    or exits with an error code.
    """
    try:
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