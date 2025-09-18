# content_processor.py
# Handles the transformation of user-provided files and text into the
# specific content block format required by the strands-agents library.

import base64
import re
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any, Union, Optional

from utils import guess_mimetype, scan_directory

def _process_single_file(file_path: Path, mimetype: str) -> Optional[Dict[str, Any]]:
    """
    Reads a single file and prepares it as a content block for the agent.
    Returns a text block for text files, or a generic binary block for others.
    """
    try:
        # For any text-based format, read the content as a string.
        if mimetype.startswith("text/"):
            logger.debug(f"Reading file '{file_path}' as text.")
            with open(file_path, "r", errors='replace') as f:
                return {"type": "text", "text": f.read()}
        
        # For all other file types, encode them as base64.
        else:
            logger.debug(f"Reading file '{file_path}' as base64-encoded binary.")
            with open(file_path, "rb") as f:
                encoded_data = base64.b64encode(f.read()).decode('utf-8')
            # The 'source' dictionary is the standard way to send binary data.
            return {
                "type": "image", # This is a generic type for binary data in strands
                "source": {
                    "type": "base64",
                    "media_type": mimetype,
                    "data": encoded_data
                }
            }
    except Exception as e:
        logger.error(f"Could not read or encode file {file_path}: {e}")
        return None


def process_path_argument(path_str: str, mimetype: Optional[str], max_files: int) -> List[tuple[str, str]]:
    """
    Centralized logic to process a path string, which can be a file, a directory,
    or a directory with glob filters. Respects the max_files limit.
    """
    found_files_with_mimetype = []
    dir_filter_pattern = re.compile(r"(.+?)\[(.+?)\]$")
    match = dir_filter_pattern.match(path_str)

    dir_path, filters = (match.group(1), [f.strip() for f in match.group(2).split(',')]) if match else (path_str, None)

    if filters and os.path.isdir(dir_path):
        logger.info(f"Directory scanning with filters: {filters} in '{dir_path}'")
        found_files = scan_directory(dir_path, limit=max_files, filters=filters)
        for f_path in found_files:
            found_files_with_mimetype.append((f_path, mimetype or guess_mimetype(f_path)))
    elif os.path.isdir(path_str):
        logger.info(f"Directory detected. Scanning '{path_str}' for text files...")
        found_files = scan_directory(path_str, limit=max_files)
        for f_path in found_files:
            found_files_with_mimetype.append((f_path, mimetype or guess_mimetype(f_path)))
    elif os.path.isfile(path_str):
        found_files_with_mimetype.append((path_str, mimetype or guess_mimetype(path_str)))
    else:
        logger.warning(f"The path '{path_str}' is not a valid file or directory. Skipping.")

    return found_files_with_mimetype


def process_startup_files(files: List[tuple[str, str]], max_files: int) -> Optional[List[Dict[str, Any]]]:
    """Processes files provided at startup into a multi-modal message list."""
    if not files:
        return None

    content: List[Dict[str, Any]] = [
        {"type": "text", "text": "The user has uploaded the following files for analysis:"}
    ]
    for file_path_str, mimetype in files:
        file_path = Path(file_path_str)
        content.append({"type": "text", "text": f"\n--- File: {file_path_str} ({mimetype}) ---\n"})
        file_block = _process_single_file(file_path, mimetype)
        if file_block:
            content.append(file_block)

    content.append({"type": "text", "text": "\nPlease acknowledge you have received these files and await my instructions."})
    
    return [{"role": "user", "content": content}] if len(content) > 2 else None


def parse_input_with_files(user_input: str, max_files: int) -> Union[str, List[Dict[str, Any]]]:
    """
    Parses user input for file(...) syntax. If no files are
    found, returns the original string. Otherwise, constructs a content list.
    """
    content: List[Dict[str, Any]] = []
    last_index = 0
    
    file_pattern = re.compile(
        r"file\((?P<quote>['\"])(?P<path>.*?)(?P=quote)\s*(?P<mimetype>\S+)?\)"
    )

    for match in file_pattern.finditer(user_input):
        text_before = user_input[last_index:match.start()].strip()
        if text_before:
            content.append({"type": "text", "text": text_before})

        path = match.group('path')
        mimetype = match.group('mimetype')
        
        remaining_slots = max_files - sum(1 for item in content if 'source' in item)
        if remaining_slots <= 0:
            logger.warning(f"In-chat file limit of {max_files} reached. Ignoring further file() calls.")
            break

        found_files_with_mimetype = process_path_argument(path, mimetype, max_files=remaining_slots)

        for file_path_str, resolved_mimetype in found_files_with_mimetype:
            file_block = _process_single_file(Path(file_path_str), resolved_mimetype)
            if file_block:
                content.append(file_block)
        
        last_index = match.end()

    if not content:
        return user_input.strip()

    text_after = user_input[last_index:].strip()
    if text_after:
        content.append({"type": "text", "text": text_after})

    if not any('source' in item for item in content):
        return "".join(item.get("text", "") for item in content)

    return content
