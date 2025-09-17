# utils.py
# Contains generic helper functions for file system operations and config discovery.

import glob
import json
import os
import mimetypes
import re
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any, Union, Optional, Tuple

def guess_mimetype(file_path: Union[str, Path]) -> str:
    """Guesses the mimetype of a file, defaulting to a binary stream."""
    mimetype, _ = mimetypes.guess_type(file_path)
    return mimetype if mimetype else 'application/octet-stream'

def is_likely_text_file(file_path: Union[str, Path]) -> bool:
    """
    Determines if a file is likely to be plain text by checking its mimetype
    and, as a fallback, sniffing the first 1KB for null bytes.
    """
    mimetype = guess_mimetype(file_path)
    if mimetype.startswith('text/'):
        return True
    # Many common text-based formats don't have a 'text/' prefix.
    if any(sub in mimetype for sub in ['json', 'xml', 'javascript', 'csv']):
        return True
    
    try:
        with open(file_path, 'rb') as f:
            # A null byte is a strong indicator of a binary file.
            return b'\0' not in f.read(1024)
    except IOError:
        return False

def scan_directory(directory: str, limit: int, filters: Optional[List[str]] = None) -> List[str]:
    """
    Recursively scans a directory for files. If filters are provided, it uses
    glob matching. Otherwise, it finds files that are likely to contain text.
    """
    found_files = []
    
    if filters:
        # Use glob matching if filters are provided
        for filter_glob in filters:
            if len(found_files) >= limit:
                break
            # Create a recursive glob pattern
            search_pattern = os.path.join(directory, '**', filter_glob)
            for file_path in glob.glob(search_pattern, recursive=True):
                if os.path.isfile(file_path):
                    found_files.append(file_path)
                    if len(found_files) >= limit:
                        break
    else:
        # Fallback to the original text file scanning logic
        for root, _, files in os.walk(directory):
            if len(found_files) >= limit:
                break
            for file in files:
                file_path = os.path.join(root, file)
                if is_likely_text_file(file_path):
                    found_files.append(file_path)
                    if len(found_files) >= limit:
                        break
                        
    return found_files[:limit]

def discover_tool_configs(directory: Optional[str]) -> List[Dict[str, Any]]:
    """Discovers and loads tool configurations from *.tools.json files."""
    if directory is None:
        logger.info("Tool discovery is disabled by command-line option.")
        return []
    if not os.path.isdir(directory):
        logger.warning(f"Tools directory not found: '{directory}'. Skipping tool discovery.")
        return []

    configs = []
    search_path = os.path.join(directory, '*.tools.json')
    for file_path in glob.glob(search_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                config_data['source_file'] = file_path # For reference in logs/UI
                configs.append(config_data)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load or parse tool config '{file_path}': {e}")
    return configs

# A data-driven list of rules for guessing the model framework.
# The first rule to match (case-insensitively) wins.
FRAMEWORK_GUESSING_RULES: List[Tuple[str, str]] = [
    ("gpt-", "openai"),
    ("claude", "anthropic"),
    ("gemini", "litellm"),
    ("google", "litellm"),
    ("/", "litellm"), # Convention for litellm models like 'ollama/llama2'
]

def guess_framework_from_model_string(model_name: str) -> str:
    """
    Makes a best guess for the model framework based on a list of rules.
    This allows for backward compatibility and convenience.
    """
    model_lower = model_name.lower()
    for condition, framework in FRAMEWORK_GUESSING_RULES:
        if condition in model_lower:
            logger.debug(f"Guessed '{framework}' framework for model '{model_name}' based on rule '{condition}'.")
            return framework
    
    # Default fallback if no rules match.
    logger.warning(f"Could not determine framework for '{model_name}' based on rules. Defaulting to 'litellm'.")
    return "litellm"
