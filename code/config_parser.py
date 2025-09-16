# config_parser.py
# Handles parsing of command-line arguments for the chatbot.

import argparse
import os
import sys
from pathlib import Path
from loguru import logger
from typing import List

from utils import guess_mimetype, scan_directory_for_text_files

# Define constants for clarity and maintainability.
DEFAULT_SYSTEM_PROMPT = (
    "You are a general assistant with access to various tools to enhance your capabilities. "
    "You are NOT a specialized assistant dedicated to any specific tool provider."
)
FILE_UPLOAD_LIMIT = 20

def _process_system_prompt(prompt_arg: str) -> tuple[str, str]:
    """
    Processes the system prompt argument, loading from a file if necessary.
    Returns the prompt content and its source description.
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

def _process_file_and_directory_args(file_args: List[List[str]]) -> List[tuple[str, str]]:
    """
    Processes the list of file/directory arguments from argparse.
    Handles recursive directory scanning and mimetype resolution.
    """
    if not file_args:
        return []

    processed_files: List[tuple[str, str]] = []
    for file_arg in file_args:
        if len(processed_files) >= FILE_UPLOAD_LIMIT:
            logger.warning(f"File limit of {FILE_UPLOAD_LIMIT} reached. Ignoring further file arguments.")
            break

        path_str = file_arg[0]
        
        if os.path.isdir(path_str):
            logger.info(f"Directory detected. Scanning '{path_str}' for text files...")
            override_mimetype = file_arg[1] if len(file_arg) > 1 and "/" in file_arg[1] else None
            if override_mimetype:
                logger.info(f"Using override mimetype '{override_mimetype}' for all files found in '{path_str}'.")

            remaining_limit = FILE_UPLOAD_LIMIT - len(processed_files)
            found_files = scan_directory_for_text_files(path_str, limit=remaining_limit)
            
            for f_path in found_files:
                mimetype_to_use = override_mimetype or guess_mimetype(f_path)
                processed_files.append((f_path, mimetype_to_use))
            logger.info(f"Found and added {len(found_files)} files from '{path_str}'.")

        elif os.path.isfile(path_str):
            mimetype = (file_arg[1] if len(file_arg) > 1 and "/" in file_arg[1] 
                        else guess_mimetype(path_str))
            processed_files.append((path_str, mimetype))
        else:
            logger.warning(f"The path '{path_str}' is not a valid file or directory. Skipping.")
            
    return processed_files

def parse_arguments() -> argparse.Namespace:
    """
    Defines and parses command-line arguments, then delegates processing.
    """
    parser = argparse.ArgumentParser(
        description="A command-line chatbot powered by Strands Agents and LiteLLM."
    )
    
    parser.add_argument(
        "-p", "--prompt",
        dest="system_prompt_arg",
        default=DEFAULT_SYSTEM_PROMPT,
        help="The system prompt for the agent. Can be a string or 'file:///path/to/prompt.txt'."
    )
    
    parser.add_argument(
        "-m", "--model",
        default="gemini/gemini-2.5-flash",
        help="The model ID to use for the agent (e.g., 'gemini/gemini-2.5-flash')."
    )

    parser.add_argument(
        "-f", "--file",
        dest="files_raw",
        nargs='+',
        action='append',
        metavar=('PATH', '[MIMETYPE]'),
        help=f"Upload a file or a directory. Scans directories recursively for text files. Limit: {FILE_UPLOAD_LIMIT} files."
    )
    
    parser.add_argument(
        "-t", "--tools",
        dest='tools_dir',
        nargs='?',
        const=None,
        default='.',
        help="Directory to load MCP configurations from. If omitted, CWD is used."
    )
    
    parser.add_argument(
        '-i', '--initial-message',
        dest='initial_message',
        type=str,
        default=None,
        help='An initial message to send. In headless mode, if omitted, reads from stdin.'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        help='Enable headless mode for scripting. Reads a message, prints the response, and exits.'
    )
    
    args = parser.parse_args()

    # --- Argument Processing ---
    if args.headless and not args.initial_message and not sys.stdin.isatty():
        logger.info("Reading initial message from stdin for headless mode...")
        args.initial_message = sys.stdin.read()
    
    args.system_prompt, args.prompt_source = _process_system_prompt(args.system_prompt_arg)
    args.files = _process_file_and_directory_args(args.files_raw or [])
            
    return args

