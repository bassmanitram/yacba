# content_processor.py
# Handles the transformation of user-provided files and text into the
# specific content block format required by the strands-agents library.

import base64
import re
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any, Union, Optional

from utils import guess_mimetype

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
        return {"type": "text", "text": f"(Error reading file: {file_path})"}

def process_startup_files(files: List[tuple[str, str]]) -> Optional[List[Dict[str, Any]]]:
    """Processes files provided at startup into a multi-modal message list."""
    if not files:
        return None

    content: List[Dict[str, Any]] = [
        {"type": "text", "text": "The user has uploaded the following files for analysis:"}
    ]
    for file_path_str, mimetype in files:
        file_path = Path(file_path_str)
        if file_path.is_file():
            # Add a separator for clarity when multiple files are uploaded.
            content.append({"type": "text", "text": f"\n--- File: {file_path_str} ({mimetype}) ---\n"})
            file_block = _process_single_file(file_path, mimetype)
            if file_block:
                content.append(file_block)
        else:
            logger.warning(f"Startup file not found and was skipped: {file_path_str}")

    content.append({"type": "text", "text": "\nPlease acknowledge you have received these files and await my instructions."})
    
    # Only return a message if files were actually processed.
    return [{"role": "user", "content": content}] if len(content) > 2 else None

def parse_input_with_files(user_input: str) -> Union[str, List[Dict[str, Any]]]:
    """
    Parses user input for file('path') syntax. If no files are
    found, returns the original string. Otherwise, constructs a content list.
    """
    content: List[Dict[str, Any]] = []
    last_index = 0
    # Regex to find file('path') or file("path") calls. Mimetype is now always guessed.
    file_pattern = re.compile(r"file\((['\"])(.*?)\1\)")

    for match in file_pattern.finditer(user_input):
        # Add any text that appeared before the file() call.
        text_before = user_input[last_index:match.start()].strip()
        if text_before:
            content.append({"type": "text", "text": text_before})

        file_path_str = match.group(2)
        mimetype = guess_mimetype(file_path_str)
        file_path = Path(file_path_str)
        
        if file_path.is_file():
            file_block = _process_single_file(file_path, mimetype)
            if file_block:
                content.append(file_block)
        else:
            logger.warning(f"File not found during chat: {file_path_str}")
            content.append({"type": "text", "text": f"(File not found at path: {file_path_str})"})
        
        last_index = match.end()

    # If no file patterns were matched, it's just plain text.
    if not content:
        return user_input.strip()

    # Add any remaining text that appeared after the last file() call.
    text_after = user_input[last_index:].strip()
    if text_after:
        content.append({"type": "text", "text": text_after})

    # Ensure the text part comes first for better model compatibility.
    content.sort(key=lambda x: 0 if x['type'] == 'text' else 1)
    return content

