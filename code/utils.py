# utils.py
# Contains generic helper functions for file system operations and config discovery.

import glob
import json
import os
import mimetypes
import fnmatch
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any, Union, Optional

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
    Recursively scans a directory for files. If filters are provided, it matches
    filenames against the glob patterns. Otherwise, it finds likely text files.
    """
    found_files = []
    for root, _, files in os.walk(directory):
        if len(found_files) >= limit:
            break
        for file in files:
            if len(found_files) >= limit:
                break
            
            file_path = os.path.join(root, file)
            
            if filters:
                # If any filter pattern matches the filename, add it.
                if any(fnmatch.fnmatch(file, pattern) for pattern in filters):
                    found_files.append(file_path)
            # If no filters, fall back to the original text-file-finding behavior.
            elif is_likely_text_file(file_path):
                found_files.append(file_path)

    return found_files

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
