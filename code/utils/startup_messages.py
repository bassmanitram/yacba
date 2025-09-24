"""
Message display functions for YACBA CLI.

Handles welcome messages, startup information, and status reporting.
"""

import sys
from typing import List, TextIO
from pathlib import Path

from yacba_types.tools import ToolSystemStatus


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
    tool_system_status: ToolSystemStatus,
    startup_files: List[tuple[str, str]],
    output_file: TextIO = sys.stdout,
):
    """
    Enhanced startup info with unified tool status reporting.
    
    Args:
        model_id: Model identifier string
        system_prompt: System prompt text
        prompt_source: Source of the system prompt
        tool_system_status: Status of tool loading
        startup_files: List of uploaded files
        output_file: Output stream for messages
    """
    
    def write(msg):
        print(msg, file=output_file)

    write("-" * 50)
    
    # Display basic configuration
    _print_basic_config(write, model_id, system_prompt, prompt_source)
    
    # Display tool status
    _print_tool_status(write, tool_system_status)
    
    # Display uploaded files
    _print_startup_files(write, startup_files)
    
    write("-" * 50)


def _print_basic_config(write_func, model_id: str, system_prompt: str, prompt_source: str):
    """Print basic configuration information."""
    first_line = system_prompt.split("\n")[0]
    ellipsis = "..." if "\n" in system_prompt else ""
    write_func(f'System Prompt (from {prompt_source}): "{first_line}{ellipsis}"')
    write_func(f"Model: {model_id}")


def _print_tool_status(write_func, tool_system_status: ToolSystemStatus):
    """Print detailed tool loading status."""
    discovery = tool_system_status.discovery_result
    successful_results = tool_system_status.successful_results
    failed_results = tool_system_status.failed_results
    missing_function_results = tool_system_status.results_with_missing_functions
    
    if discovery.total_files_scanned > 0 or len(successful_results) > 0 or len(failed_results) > 0:
        write_func("\nTool System Status:")
        write_func(f"  Configuration files scanned: {discovery.total_files_scanned}")
        write_func(f"  Valid configurations loaded: {len(discovery.successful_configs)}")
        write_func(f"  Configuration parsing failures: {len(discovery.failed_configs)}")
        write_func(f"  Tools successfully loaded: {tool_system_status.total_tools_loaded}")
        
        # Report successful tool loading
        if successful_results:
            write_func("  ✓ Successful tool loading:")
            for result in successful_results:
                source_name = Path(result.source_file).name
                write_func(f"    • {result.config_id} ({source_name}): {len(result.tools)} tools")
        
        # Report configuration parsing failures
        if discovery.has_failures:
            write_func("  ✗ Configuration parsing failures:")
            for failed in discovery.failed_configs:
                source_name = Path(failed['file_path']).name
                write_func(f"    • {source_name}: {failed['error']}")
        
        # Report tool loading failures
        if failed_results:
            write_func("  ✗ Tool loading failures:")
            for result in failed_results:
                source_name = Path(result.source_file).name
                write_func(f"    • {result.config_id} ({source_name}): {result.error_message}")
        
        # Report missing functions
        if missing_function_results:
            write_func("  ⚠ Missing requested functions:")
            for result in missing_function_results:
                if result.has_missing_functions:
                    source_name = Path(result.source_file).name
                    missing_list = ', '.join(result.missing_functions)
                    write_func(f"    • {result.config_id} ({source_name}): {missing_list}")
    else:
        write_func("Available Tools: None")


def _print_startup_files(write_func, startup_files: List[tuple[str, str]]):
    """Print information about uploaded startup files."""
    if startup_files:
        write_func(f"\nUploaded Files ({len(startup_files)}):")
        for path, media_type in startup_files:
            write_func(f"  - {path} ({media_type})")
    else:
        write_func("Uploaded Files: None")