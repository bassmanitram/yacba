"""
YACBA - Yet Another ChatBot Agent

A flexible chatbot system that integrates with strands-agents for AI conversation
and tool usage, with support for multiple model providers and conversation management.
"""

import asyncio
import sys
from typing import NoReturn

# Configure logging early
from utils.logging import get_logger  # noqa: E402
from utils.exceptions import log_exception  # noqa: E402
from utils.session_utils import get_history_path  # noqa: E402

logger = get_logger(__name__)

# Completion imports
from prompt_toolkit.completion import merge_completers  # noqa: E402

# YACBA core functionality - configuration and startup
from adapters.repl_toolkit.completer import YacbaCompleter  # noqa: E402
from config import parse_config, YacbaConfig  # noqa: E402
from utils.startup_messages import (  # noqa: E402
    print_startup_info,
    print_welcome_message,
)
from yacba_types import ExitCode  # noqa: E402

# strands_agent_factory integration
from strands_agent_factory import AgentFactory  # noqa: E402
from strands_agent_factory.core.agent import AgentProxy  # noqa: E402
from adapters.strands_factory import YacbaToStrandsConfigConverter  # noqa: E402

# repl_toolkit integration
from repl_toolkit import AsyncREPL, HeadlessREPL  # noqa: E402
from repl_toolkit.completion import (  # noqa: E402
    PrefixCompleter,
    ShellExpansionCompleter,
)
from adapters.repl_toolkit import YacbaBackend, YacbaActionRegistry  # noqa: E402


def _create_stdout_printer():
    """Create a simple stdout printer for headless mode."""
    import sys

    def printer(text: str) -> None:
        print(text, file=sys.stdout, flush=True)

    return printer


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
        agent = (
            factory.create_agent()
        )  # This should be synchronous after initialization

        # Create action registry with backend
        # Create action registry with appropriate printer
        printer = _create_stdout_printer() if config.headless else print
        action_registry = YacbaActionRegistry(printer=printer)

        # Run in appropriate mode
        if config.headless:
            await _run_headless_mode(agent, action_registry, config, strands_config)
        else:
            await _run_interactive_mode(agent, action_registry, config, strands_config)

    except Exception as e:
        log_exception(logger, "fatal_error_in_agent_lifecycle", e)
        sys.exit(ExitCode.FATAL_ERROR)


def _build_conversation_manager_info(config: YacbaConfig) -> str:
    """
    Build detailed conversation manager information string.

    Args:
        config: YACBA configuration

    Returns:
        str: Formatted conversation manager information
    """
    cm_type = config.conversation_manager_type
    
    if cm_type == "null":
        return "Conversation Manager: null (no management)"
    elif cm_type == "sliding_window":
        return f"Conversation Manager: sliding_window (size: {config.sliding_window_size} messages)"
    elif cm_type == "summarizing":
        summary_model = config.summarization_model or config.model_string
        return (
            f"Conversation Manager: summarizing "
            f"(preserve: {config.preserve_recent_messages} messages, "
            f"ratio: {config.summary_ratio}, "
            f"model: {summary_model})"
        )
    else:
        return f"Conversation Manager: {cm_type}"


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

        # Build detailed conversation manager info
        cm_info = _build_conversation_manager_info(config)

        # Use YACBA's existing startup message function
        print_startup_info(
            model_id=model_id,
            system_prompt=system_prompt,
            prompt_source=prompt_source,
            tools=agent_proxy.tool_specs or [],
            startup_files=config.files_to_upload or [],
            conversation_manager_info=cm_info,
            session_name=config.session_name,
        )

    except Exception as e:
        logger.error("error_printing_startup_info", error=str(e))


async def _run_headless_mode(
    agent: AgentProxy,
    action_registry: YacbaActionRegistry,
    config: YacbaConfig,
    strands_config,
) -> None:
    """
    Run in headless mode using repl_toolkit.

    Args:
        agent: The agent proxy
        action_registry: The action registry
        config: YACBA configuration
        strands_config: Converted strands_agent_factory configuration
    """
    logger.info("starting_headless_mode")

    repl = HeadlessREPL(
        action_registry=action_registry,
    )

    with agent as agent_context:
        # Create backend adapter
        backend = YacbaBackend(agent_context, strands_config)

        # Run the async REPL
        return await repl.run(
            backend=backend,
            initial_message="Evaluate" if agent.has_initial_messages else None,
        )


async def _run_interactive_mode(
    agent: AgentProxy,
    action_registry: YacbaActionRegistry,
    config: YacbaConfig,
    strands_config,
) -> None:
    """
    Run in interactive mode using repl_toolkit.

    Args:
        agent: The agent proxy
        action_registry: The action registry
        config: YACBA configuration
        strands_config: Converted strands_agent_factory configuration
    """
    logger.info("starting_interactive_mode")

    # Create individual completers
    command_completer = PrefixCompleter(
        words=sorted(
            action_registry.list_commands()
        ),  # Sort for better tab completion UX
        prefix="/",
        ignore_case=True,
    )

    shell_completer = ShellExpansionCompleter(
        timeout=2.0, multiline_all=True, max_lines=30
    )

    file_completer = YacbaCompleter()

    # Merge completers: commands first, then shell expansion, then file paths
    completer = merge_completers([command_completer, shell_completer, file_completer])

    # Get history path using centralized utility
    history_path = get_history_path(config.session_name)

    repl = AsyncREPL(
        action_registry=action_registry,
        completer=completer,
        prompt_string=config.cli_prompt or "User: ",
        history_path=history_path,
        enable_system_prompt=True,
        enable_suspend=True,
    )

    with agent as agent_context:
        # Create backend adapter
        backend = YacbaBackend(agent_context, strands_config)

        # Print startup information
        # Print welcome message for interactive mode
        print_welcome_message()

        _print_startup_info(config, agent_context)

        # Run the async REPL
        return await repl.run(
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
        # Welcome message printed after config parsing (if not headless)

        # Parse configuration
        config = parse_config()

        # Run the main application
        asyncio.run(_run_agent_lifecycle(config))

    except KeyboardInterrupt:
        logger.info("application_interrupted_by_user")
        sys.exit(ExitCode.USER_INTERRUPT)
    except Exception as e:
        log_exception(logger, "fatal_error", e)
        sys.exit(ExitCode.FATAL_ERROR)


if __name__ == "__main__":
    main()
