"""
Handles parsing of command-line arguments for the chatbot.
Migrated to use focused type system with --show-tool-use feature.

    # Performance optimization options
    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear the performance cache before starting'
    )
    
    parser.add_argument(
        '--show-perf-stats',
        action='store_true',
        help='Display performance statistics at the end'
    )
    
    parser.add_argument(
        '--disable-cache',
        action='store_true',
        help='Disable caching for debugging purposes'
    )
"""

import argparse
import os
import sys
import json
from pathlib import Path
from loguru import logger
from typing import List, Tuple

# Import focused types
from yacba_types.config import ModelConfig, ToolConfig, FileUpload
from yacba_types.base import PathLike
from content_processor import process_path_argument
from yacba_config import YacbaConfig
from general_utils import discover_tool_configs

# Define constants for clarity and maintainability.
DEFAULT_SYSTEM_PROMPT = (
    "You are a general assistant with access to various tools to enhance your capabilities. "
    "You are NOT a specialized assistant dedicated to any specific tool provider."
)
DEFAULT_FILE_UPLOAD_LIMIT = 20

def _process_system_prompt(prompt_arg: str) -> Tuple[str, str]:
    """
    Processes the system prompt argument, loading from a file if necessary.
    Returns the prompt content and its source description.
    
    Args:
        prompt_arg: The prompt argument (string or file:// URI)
        
    Returns:
        Tuple of (prompt_content, source_description)
    """
    if prompt_arg == DEFAULT_SYSTEM_PROMPT:
        return DEFAULT_SYSTEM_PROMPT, "default"
    
    if prompt_arg.startswith("file://"):
        file_path_str = prompt_arg[7:]
        source = f"file '{file_path_str}'"
        try:
            with open(Path(file_path_str), 'r', encoding='utf-8') as f:
                return f.read(), source
        except (IOError, FileNotFoundError) as e:
            logger.error(f"Could not read system prompt file: {e}. Using default.")
            return DEFAULT_SYSTEM_PROMPT, "default (fallback)"
    
    return prompt_arg, "command-line"

def _process_file_args(file_args: List[List[str]], max_files: int) -> List[FileUpload]:
    """
    Processes the list of file/directory arguments from argparse into a flat list of file uploads.
    
    Args:
        file_args: List of file argument lists from argparse
        max_files: Maximum number of files to process
        
    Returns:
        List of FileUpload objects
    """
    if not file_args:
        return []

    processed_files: List[FileUpload] = []
    for file_arg in file_args:
        remaining_slots = max_files - len(processed_files)
        if remaining_slots <= 0:
            logger.warning(f"File limit of {max_files} reached. Ignoring further file arguments.")
            break
        
        path_str = file_arg[0]
        mimetype = file_arg[1] if len(file_arg) > 1 else None
        
        # Process path and convert to FileUpload format
        found = process_path_argument(path_str, mimetype, max_files=remaining_slots)
        for file_path, file_mimetype in found:
            file_upload: FileUpload = {
                "path": file_path,
                "mimetype": file_mimetype,
                "size": None  # Will be calculated later if needed
            }
            processed_files.append(file_upload)

    return processed_files

def _process_model_config(config_file: str, config_vals: List[str]) -> ModelConfig:
    """
    Loads model configuration from a file and overrides it with individual values.
    
    Args:
        config_file: Path to JSON config file
        config_vals: List of key:value configuration overrides
        
    Returns:
        ModelConfig dictionary
    """
    config: ModelConfig = {}
    
    if config_file:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                # Validate that loaded config matches ModelConfig structure
                config.update(loaded_config)
            logger.info(f"Loaded model configuration from '{config_file}'.")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Could not load or parse model config file '{config_file}': {e}")

    for val in config_vals or []:
        if ':' not in val:
            logger.warning(f"Invalid config value '{val}'. Must be in 'key:value' format. Skipping.")
            continue
        
        key, value_str = val.split(':', 1)
        
        # Type conversion for common config values
        if value_str.lower() == 'true': 
            value = True
        elif value_str.lower() == 'false': 
            value = False
        else:
            try:
                value = float(value_str)
                if value.is_integer(): 
                    value = int(value)
            except ValueError:
                value = value_str
        
        config[key] = value  # type: ignore
        logger.info(f"Set model config override: {key} = {value}")
        
    return config

def parse_config() -> YacbaConfig:
    """
    Defines and parses command-line arguments, then populates and returns
    a YacbaConfig object with proper type safety.
    
    Returns:
        Fully configured and validated YacbaConfig object
    """
    # Determine default model from environment variable or hard-coded value
    default_model = os.environ.get("YACBA_MODEL_ID", "litellm:gemini/gemini-1.5-flash")

    parser = argparse.ArgumentParser(
        description="A command-line chatbot powered by Strands Agents."
    )
    
    parser.add_argument(
        "-p", "--prompt",
        dest="system_prompt_arg",
        default=DEFAULT_SYSTEM_PROMPT,
        help="The system prompt for the agent. Can be a string or 'file:///path/to/prompt.txt'."
    )
    
    parser.add_argument(
        "-m", "--model",
        default=default_model,
        help=f"The model to use, in <framework>:<model_id> format. Default: {default_model} (or from YACBA_MODEL_ID)."
    )

    parser.add_argument(
        "-f", "--file",
        dest="files_raw",
        nargs='+',
        action='append',
        metavar=('PATH', '[MIMETYPE]'),
        help=f"Upload a file or a directory. Scans directories recursively. "
             f"For directories, you can add filters like 'my_dir[*.py,*.js]'. Limit: {DEFAULT_FILE_UPLOAD_LIMIT} files."
    )

    parser.add_argument(
        "--max-files",
        type=int,
        default=DEFAULT_FILE_UPLOAD_LIMIT,
        help=f"Maximum number of files to upload. Default: {DEFAULT_FILE_UPLOAD_LIMIT}."
    )
    
    parser.add_argument(
        "-t", "--tools",
        dest='tools_dir',
        nargs='?',
        const=None,
        default='.',
        help="Directory to load tool configurations (*.tools.json) from. "
             "Provide the flag without a path to disable tool discovery."
    )
    
    parser.add_argument(
        '-i', '--initial-message',
        dest='initial_message',
        type=str,
        default=None,
        help='An initial message to send. In headless mode, if omitted, reads from stdin.'
    )
    
    parser.add_argument(
        '--session-name',
        type=str,
        default=None,
        help='Load a session on startup and save it on exit. File is <name>.yacba-session.json.'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        help='Enable headless mode for scripting. Reads a message, prints the response, and exits.'
    )

    parser.add_argument(
        '--model-config',
        type=str,
        default=None,
        help='Path to a JSON file with ad-hoc configuration for the model.'
    )

    parser.add_argument(
        '-c', '--config-val',
        dest='config_vals',
        action='append',
        metavar='KEY:VALUE',
        help="Set a single model configuration value (e.g., 'temperature:0.8')."
    )
    
    parser.add_argument(
        '-l', '--legacy-prompt',
        dest='emulate_system_prompt',
        action='store_true',
        help='Use legacy mode for system prompts by injecting it into the first user message. For models that do not support native system prompts.'
    )
    
    
    parser.add_argument(
        '--show-tool-use',
        action='store_true',
        help='Show verbose tool execution feedback. By default, tool use details are hidden for cleaner output.'
    )

    # Performance optimization options
    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear the performance cache before starting'
    )
    
    parser.add_argument(
        '--show-perf-stats',
        action='store_true',
        help='Display performance statistics at the end'
    )
    
    parser.add_argument(
        '--disable-cache',
        action='store_true',
        help='Disable caching for debugging purposes'
    )

    args = parser.parse_args()

    # Handle stdin input for headless mode
    if args.headless and args.initial_message is None:
        args.initial_message = sys.stdin.read()

    # Process file arguments
    files_to_upload = _process_file_args(args.files_raw or [], args.max_files)

    # Process system prompt
    system_prompt, prompt_source = _process_system_prompt(args.system_prompt_arg)

    # Process model config
    model_config = _process_model_config(args.model_config, args.config_vals)

    # Discover tool configurations
    tool_configs = discover_tool_configs(args.tools_dir)

    return YacbaConfig(
        model_string=args.model,
        system_prompt=system_prompt,
        prompt_source=prompt_source,
        tool_configs=tool_configs,
        startup_files_content=None,  # Will be populated in main yacba.py
        headless=args.headless,
        model_config=model_config,
        session_name=args.session_name,
        emulate_system_prompt=args.emulate_system_prompt,
        show_tool_use=args.show_tool_use,
        initial_message=args.initial_message,
        max_files=args.max_files,
        files_to_upload=files_to_upload,
        clear_cache=args.clear_cache,
        show_perf_stats=args.show_perf_stats,
        disable_cache=args.disable_cache,
    )
