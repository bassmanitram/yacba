# content_processor.py
# Handles the transformation of user-provided files and text into the
# specific content block format required by the strands-agents library.

from mimetypes import guess_extension
import re
import os
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any, Union, Optional, Generator

from utils.file_utils import guess_mimetype, is_likely_text_file, resolve_glob, load_file_content

# Define a reasonable file size limit to avoid memory issues (e.g., 10MB)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Pre-compile regex patterns at module level for performance
FILE_PATTERN = re.compile(
    r"file\((?P<quote>['\"])(?P<path>.*?)(?P=quote)\s*(?P<mimetype>\S+)?\)"
)

DOCUMENT_TYPES = [ 'pdf', 'csv', 'doc', 'docx', 'xls', 'xlsx', 'html', 'txt', 'md' ]

def _process_single_file(file_path: Path, mimetype: str) -> Optional[Dict[str, Any]]:
    # Skip files that exceed the size limit
    if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
        logger.warning(f"Skipping file '{file_path}' because it exceeds the {MAX_FILE_SIZE_BYTES / (1024*1024):.0f}MB size limit.")
        return {
            "text": f"\n[Content of file '{file_path.name}' was skipped because it is too large.]\n"
        }

    detected_mimetype = mimetype or guess_mimetype(file_path) or "application/octet-stream"
    format = (guess_extension(detected_mimetype) or ".bin")[1:]
    likely_text = is_likely_text_file(file_path)
    file_bytes = load_file_content(file_path, 'binary')
    
    # Video files
    if detected_mimetype.startswith("video/"):
        return {
            "video": {
                "format": format,
                "source": {"bytes": file_bytes}
            }
        }

    # Image files
    if detected_mimetype.startswith("image/"):
        return {
            "image": {
                "format": format,
                "source": {"bytes": file_bytes}
            }
        }

    logger.debug(f"format check for file {file_path}: {format}")
    # Known document types
    if format in DOCUMENT_TYPES:
        return {
            "document": {
                "name": str(file_path),
                "format": format,
                "source": {"bytes": file_bytes}
            }
        }

    # Other text files
    if likely_text:
        return {
            "document": {
                "name": str(file_path),
                "format": "txt",
                "source": {"bytes": file_bytes}
            }
        }

    # Fallback: treat as binary image
    return {
        "image": {
            "format": format,
            "source": {"bytes": file_bytes}
        }
    }

def process_path_argument(path_str: str, mimetype: Optional[str], max_files: int) -> List[tuple[str, str]]:
    """
    Centralized logic to process a path string, which can be a file, a directory,
    or a directory with glob filters. Respects the max_files limit.
    Uses the unified glob resolver to eliminate code duplication.
    """
    # Use the existing resolve_glob function instead of duplicating bracket parsing logic
    try:
        resolved_files = resolve_glob(path_str)
        logger.debug(f"Resolved glob pattern '{path_str}' to {len(resolved_files)} files")
    except Exception as e:
        logger.warning(f"Error resolving glob pattern '{path_str}': {e}")
        return []

    # Apply file limit and ensure they are actually files
    found_files_with_mimetype = []
    for file_path in resolved_files:
        if len(found_files_with_mimetype) >= max_files:
            logger.info(f"File limit of {max_files} reached, stopping file resolution")
            break

        if os.path.isfile(file_path):
            detected_mimetype = mimetype or guess_mimetype(file_path)
            found_files_with_mimetype.append((file_path, detected_mimetype))
        else:
            logger.debug(f"Skipping non-file path: {file_path}")

    return found_files_with_mimetype


def files_to_content_blocks(
    files: List[tuple[str, str]],
    add_headers: bool = True,
    max_files: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Convert a list of (filepath, mimetype) tuples to content blocks.
    Used by both startup processing and inline file parsing.
    """
    if not files:
        return []

    content_blocks = []
    processed_count = 0

    for file_path_str, mimetype in files:
        if max_files and processed_count >= max_files:
            break

        file_path = Path(file_path_str)

        # Add header if requested
        if add_headers:
            content_blocks.append({
                "type": "text",
                "text": f"\n--- File: {file_path_str} ({mimetype}) ---\n"
            })

        # Process the file
        file_block = _process_single_file(file_path, mimetype)
        if file_block:
            content_blocks.append(file_block)
            processed_count += 1

    return content_blocks

def debug_print_content_blocks(blocks: List[Dict[str, Any]]) -> None:
    """Utility function to print content blocks for debugging."""
    for block in blocks:
        if block.get("text") is not None:
            logger.debug(f"Text Block: {block['text'][:100]}...")  # Print first 100 chars
        elif "image" in block:
            logger.debug(f"Image Block: format={block['image']['format']}, size={len(block['image']['source']['bytes'])} bytes")
        elif "video" in block:
            logger.debug(f"Video Block: format={block['video']['format']}, size={len(block['video']['source']['bytes'])} bytes")
        elif "document" in block:
            logger.debug(f"Document Block: name={block['document']['name']}, format={block['document']['format']}, size={len(block['document']['source']['bytes'])} bytes")
        else:
            logger.debug(f"Unknown Block Type: {block}")
    return "Block count: " + str(len(blocks))

def parse_input_with_files(user_input: str, max_files: int) -> Union[str, List[Dict[str, Any]]]:
    """Parses user input for file(...) syntax."""
    content: List[Dict[str, Any]] = []
    last_index = 0

    for match in FILE_PATTERN.finditer(user_input):
        # Add text before file reference
        text_before = user_input[last_index: match.start()].strip()
        if text_before:
            content.append({"type": "text", "text": text_before})

        # Process file reference
        path = match.group('path')
        mimetype = match.group('mimetype')

        remaining_slots = max_files - sum(1 for item in content if 'source' in item)
        if remaining_slots <= 0:
            logger.warning("File limit reached. Ignoring further file() calls.")
            break

        # Use unified file processing
        files_list = process_path_argument(path, mimetype, max_files=remaining_slots)
        logger.debug(f"Referenced file list: {files_list}")
        file_blocks = files_to_content_blocks(files_list, add_headers=False, max_files=remaining_slots)
        logger.debug(debug_print_content_blocks(file_blocks))
        content.extend(file_blocks)

        last_index = match.end()

    if not content:
        logger.debug("No file() patterns found in input.")
        return user_input.strip()

    text_after = user_input[last_index:].strip()
    if text_after:
        content.append({"text": text_after})

    logger.debug(debug_print_content_blocks(content))
    
    return content
