"""
Message display functions for YACBA CLI.

Handles welcome messages, startup information, and status reporting.
"""

import sys
from typing import Any, Dict, List, TextIO, Optional
from pathlib import Path
from strands_agent_factory.tools import EnhancedToolSpec


def print_welcome_message():
    """Prints the initial welcome message and instructions to stdout."""
    print("Welcome to Yet Another ChatBot Agent!")
    print("Type 'exit' or 'quit' to end. Type /help for a list of commands.")
    print("Use Enter to add new lines. Use Alt+Enter or Ctrl+J to send messages.")
    print("To upload a file in-chat, use the format: file('path/to/file.ext')")


def print_startup_info(
    model_id: str,
    system_prompt: str,
    prompt_source: str,
    tools: List[Dict[str, Any]],
    startup_files: List[tuple[str, str]],
    conversation_manager_info: Optional[str] = None,
    output_file: TextIO = sys.stdout,
):
    """
    Enhanced startup info with unified tool status reporting and conversation manager info.

    Args:
        model_id: Model identifier string
        system_prompt: System prompt text
        prompt_source: Source of the system prompt
        tools: List of tool specification dictionaries
        startup_files: List of uploaded files
        conversation_manager_info: Information about conversation manager configuration
        output_file: Output stream for messages
    """

    def write(msg):
        print(msg, file=output_file)

    write("-" * 50)

    # Display basic configuration
    _print_basic_config(write, model_id, system_prompt, prompt_source)

    # Display conversation manager configuration
    if conversation_manager_info:
        _print_conversation_manager_info(write, conversation_manager_info)

    # Display tool status
    _print_tool_status(write, tools)

    # Display A2A servers
    _print_a2a_servers(write, tools)

    # Display uploaded files
    _print_startup_files(write, startup_files)

    write("-" * 50)


def _print_basic_config(
    write_func, model_id: str, system_prompt: str, prompt_source: str
):
    """Print basic configuration information."""
    first_line = system_prompt.split("\n")[0]
    ellipsis = "..." if "\n" in system_prompt else ""
    write_func(f'System Prompt (from {prompt_source}): "{first_line}{ellipsis}"')
    write_func(f"Model: {model_id}")


def _print_conversation_manager_info(write_func, conversation_manager_info: str):
    """Print conversation manager configuration information."""
    write_func(f"{conversation_manager_info}")


def _print_tool_status(write_func, tools: List[EnhancedToolSpec]):
    """Print tool system status information."""

    # Exclude A2A tools from regular tool display since they always have
    # the same 3 generic tools (a2a_discover_agent, a2a_list_discovered_agents, a2a_send_message)
    # Users care about the agent URLs, not the generic tool names
    non_a2a_tools = [t for t in tools if t.get("type") != "a2a"]

    # Filter the non-A2A tools for different categories
    successful_loads = [
        t for t in non_a2a_tools if "tool_names" in t and not t.get("error")
    ]
    failed_loads = [t for t in non_a2a_tools if t.get("error")]
    no_tools = [t for t in non_a2a_tools if "tool_names" in t and not t["tool_names"]]

    if tools:  # Check original tools list for presence
        write_func("\nTool System Status:")
        write_func(f"  Configuration files scanned: {len(tools)}")
        write_func(
            f"  Valid configurations loaded: {len([t for t in tools if 'tool_names' in t and not t.get('error')])}"
        )
        write_func(
            f"  Tools successfully loaded: {sum(len(t['tool_names']) for t in [t for t in tools if 'tool_names' in t and t['tool_names']])}"
        )

        # Report successful tool loading (excluding A2A)
        if successful_loads:
            write_func("  Successful tool loading:")
            for spec in successful_loads:
                tool_id = spec.get("id", "unknown")
                source_file = spec.get("source_file", "unknown")
                tool_names = spec.get("tool_names", [])
                write_func(
                    f"    {tool_id} ({Path(source_file).name}): {len(tool_names)} tools - {', '.join(tool_names)}"
                )

        # Report configurations with no usable tools (excluding A2A)
        if no_tools:
            write_func("  No usable tools found:")
            for spec in no_tools:
                tool_id = spec.get("id", "unknown")
                source_file = spec.get("source_file", "unknown")
                write_func(
                    f"    {tool_id} ({Path(source_file).name}): No tools available"
                )

        # Report configuration parsing failures (excluding A2A)
        if failed_loads:
            write_func("  Configuration failures:")
            for spec in failed_loads:
                tool_id = spec.get("id", "unknown")
                source_file = spec.get("source_file", "unknown")
                error = spec.get("error", "unknown error")
                write_func(f"    {tool_id} ({Path(source_file).name}): {error}")
    else:
        write_func("Available Tools: None")


def _print_a2a_servers(write_func, tools: List[EnhancedToolSpec]):
    """Print A2A server information."""
    a2a_tools = [t for t in tools if t.get("type") == "a2a" and not t.get("error")]

    if a2a_tools:
        write_func("\nA2A Servers:")
        total_agents = sum(len(t.get("urls", [])) for t in a2a_tools)
        write_func(f"  Total A2A agents available: {total_agents}")

        for spec in a2a_tools:
            provider_id = spec.get("id", "unknown")
            source_file = spec.get("source_file", "unknown")
            urls = spec.get("urls", [])
            write_func(f"  {provider_id} ({Path(source_file).name}):")
            for url in urls:
                write_func(f"    - {url}")


def _print_startup_files(write_func, startup_files: List[tuple[str, str]]):
    """Print information about uploaded startup files."""
    if startup_files:
        write_func(f"\nUploaded Files ({len(startup_files)}):")
        for path, media_type in startup_files:
            write_func(f"  - {path} ({media_type})")
    else:
        write_func("Uploaded Files: None")
