# content_processor.py
# Handles the transformation of user-provided files and text into the
# specific content block format required by the strands-agents library.

import os
import base64
import re
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any, Union, Optional

from utils import guess_mimetype, scan_directory

def _process_single_file(file_path: Path, mimetype: str) -> Optional[Dict[str, Any]]:
    """
    Reads a single file and prepares it in the generic content block format.
    Transformation for specific frameworks is handled by framework adapters.
    """
    try:
        if mimetype.startswith("text/"):
            logger.debug(f"Reading file '{file_path}' as text.")
            with open(file_path, "r", errors='replace') as f:
                return {"type": "text", "text": f.read()}
        else:
            logger.debug(f"Reading file '{file_path}' as base64-encoded binary.")
            with open(file_path, "rb") as f:
                encoded_data = base64.b64encode(f.read()).decode('utf-8')
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mimetype,
                    "data": encoded_data
                }
            }
    except Exception as e:
        logger.error(f"Could not read or encode file {file_path}: {e}")
        return {"type": "text", "text": f"(Error reading file: {file_path})"}

def process_path_argument(path_str: str, mimetype_override: Optional[str], max_files: int) -> List[Dict[str, Any]]:
    """
    Processes a single file or directory path string.
    Returns a list of content blocks in the generic format.
    """
    content: List[Dict[str, Any]] = []
    dir_filter_pattern = re.compile(r"(.+?)\[(.+?)\]$")
    match = dir_filter_pattern.match(path_str)
    
    # Correctly determine the directory path whether filters are present or not
    dir_path_if_match = match.group(1) if match else path_str
    
    is_dir = os.path.isdir(dir_path_if_match)

    if is_dir:
        dir_path, filters = (match.group(1), [f.strip() for f in match.group(2).split(',')]) if match else (path_str, None)
        found_files = scan_directory(dir_path, limit=max_files, filters=filters)
        for f_path in found_files:
            mimetype = mimetype_override or guess_mimetype(f_path)
            file_block = _process_single_file(Path(f_path), mimetype)
            if file_block:
                content.append(file_block)
    elif os.path.isfile(path_str):
        mimetype = mimetype_override or guess_mimetype(path_str)
        file_block = _process_single_file(Path(path_str), mimetype)
        if file_block:
            content.append(file_block)
    else:
        logger.warning(f"Path not found: '{path_str}'")
        content.append({"type": "text", "text": f"(File or directory not found at path: {path_str})"})
    
    return content

def process_startup_files(files_raw: List[List[str]], max_files: int) -> Optional[List[Dict[str, Any]]]:
    """Processes files provided at startup into a multi-modal message list."""
    if not files_raw:
        return None

    all_file_content: List[Dict[str, Any]] = []
    for file_arg in files_raw:
        path, mimetype = file_arg[0], file_arg[1] if len(file_arg) > 1 else None
        
        remaining_limit = max_files - len(all_file_content)
        if remaining_limit <= 0:
            break
            
        all_file_content.extend(process_path_argument(path, mimetype, remaining_limit))

    if not all_file_content:
        return None

    user_message_content: List[Dict[str, Any]] = [
        {"type": "text", "text": "The user has uploaded the following files for analysis. Please acknowledge you have received them and await instructions."}
    ]
    user_message_content.extend(all_file_content)
    
    return [{"role": "user", "content": user_message_content}]

def parse_input_with_files(user_input: str, max_files: int = 10) -> Union[str, List[Dict[str, Any]]]:
    """
    Parses user input for file(...) syntax, returning a structured content list.
    Supports file('path') and file('path' mimetype).
    """
    content_parts: List[Union[str, List[Dict[str, Any]]]] = []
    last_index = 0
    # Regex updated to handle a quoted path followed by an optional, unquoted mimetype.
    file_pattern = re.compile(r"file\((['\"])(.*?)\1(?:\s+([\w\/.-]+))?\)")

    for match in file_pattern.finditer(user_input):
        text_before = user_input[last_index:match.start()].strip()
        if text_before:
            content_parts.append(text_before)

        path_str = match.group(2)
        mimetype_override = match.group(3) # Group 3 is now the optional mimetype.
        
        file_blocks = process_path_argument(path_str, mimetype_override, max_files)
        content_parts.append(file_blocks)
        
        last_index = match.end()

    if not content_parts:
        return user_input.strip()

    text_after = user_input[last_index:].strip()
    if text_after:
        content_parts.append(text_after)

    final_content: List[Dict[str, Any]] = []
    for part in content_parts:
        if isinstance(part, str):
            final_content.append({"type": "text", "text": part})
        elif isinstance(part, list):
            final_content.extend(part)
            
    return final_content
