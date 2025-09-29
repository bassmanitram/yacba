import base64
import glob
import json
import mimetypes
import os
from pathlib import Path
import re
from typing import Dict, List, Optional, Any
import yaml

from loguru import logger

from .performance_utils import timed_operation, perf_monitor, cached_operation
from yacba_types.base import PathLike


def guess_mimetype(file_path: PathLike) -> str:
    """
    Guess the MIME type of a file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME type string, defaults to 'application/octet-stream'
    """
    mimetype, _ = mimetypes.guess_type(str(file_path))
    return mimetype or 'application/octet-stream'

def is_likely_text_file(file_path: PathLike) -> bool:
    """
    Determine if a file is likely to contain text content.
    Uses file extension and basic heuristics.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file is likely text, False otherwise
    """
    path = Path(file_path)
    
    # Check if file exists and is a regular file
    if not path.exists() or not path.is_file():
        return False
    
    # Common text file extensions
    text_extensions = {
        '.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
        '.ini', '.cfg', '.conf', '.log', '.csv', '.tsv', '.sql', '.sh', '.bat', '.ps1',
        '.c', '.cpp', '.h', '.hpp', '.java', '.cs', '.php', '.rb', '.go', '.rs', '.swift',
        '.kt', '.scala', '.clj', '.hs', '.ml', '.fs', '.vb', '.pl', '.r', '.m', '.tex',
        '.rst', '.adoc', '.org', '.wiki', '.dockerfile', '.gitignore', '.gitattributes',
        '.editorconfig', '.eslintrc', '.prettierrc', '.babelrc', '.tsconfig', '.package',
        '.lock', '.toml', '.properties', '.env', '.example', '.sample', '.template'
    }
    
    # Check extension
    if path.suffix.lower() in text_extensions:
        return True
    
    # Check for files without extensions that are commonly text
    if not path.suffix:
        common_text_names = {
            'readme', 'license', 'changelog', 'authors', 'contributors', 'makefile',
            'dockerfile', 'jenkinsfile', 'vagrantfile', 'gemfile', 'rakefile', 'procfile'
        }
        if path.name.lower() in common_text_names:
            return True
    
    # For small files, do a quick binary check
    try:
        if path.stat().st_size > 1024 * 1024:  # Skip files larger than 1MB
            return False
        
        with open(path, 'rb') as f:
            chunk = f.read(1024)  # Read first 1KB
            
        # Check for null bytes (common in binary files)
        if b'\x00' in chunk:
            return False
        
        # Check if most bytes are printable ASCII or common UTF-8
        try:
            chunk.decode('utf-8')
            return True
        except UnicodeDecodeError:
            # Try to decode as latin-1 (more permissive)
            try:
                chunk.decode('latin-1')
                # Check if it looks like text (mostly printable characters)
                printable_count = sum(1 for b in chunk if 32 <= b <= 126 or b in (9, 10, 13))
                return printable_count / len(chunk) > 0.7
            except UnicodeDecodeError:
                return False
                
    except (OSError, IOError):
        return False

@cached_operation("structured_file_load")
def load_structured_file(file_path: PathLike, file_format: str = 'auto') -> Dict[str, Any]:
    """
    Load and parse structured configuration files (JSON/YAML) with caching.
    
    Args:
        file_path: Path to the configuration file
        file_format: 'json', 'yaml', or 'auto' (detect from extension)
    
    Returns:
        Parsed configuration as dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML parsing fails
        json.JSONDecodeError: If JSON parsing fails
        ValueError: If unsupported file format
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    if file_format == 'auto':
        file_format = 'yaml' if path.suffix.lower() in ('.yaml', '.yml') else 'json'
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            if file_format == 'yaml':
                result = yaml.safe_load(f)
                return result if result is not None else {}
            elif file_format == 'json':
                return json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in {file_path}: {e}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {file_path}: {e}", doc="", pos=0)

@cached_operation("file_content_load")
def load_file_content(file_path: PathLike, content_type: str = 'auto') -> Dict[str, Any]:
    """
    Load file contents with format detection and caching.
    
    Args:
        file_path: Path to the file
        content_type: 'text', 'binary', or 'auto' (detect from file analysis)
        
    Returns:
        Dictionary with 'type' and 'content' keys, plus optional metadata
        
    Raises:
        FileNotFoundError: If file doesn't exist
        OSError: If file cannot be read
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if content_type == 'auto':
        content_type = 'text' if is_likely_text_file(path) else 'binary'
    
    try:
        if content_type == 'text':
            with open(path, 'r', errors='replace') as f:
                return {"type": "text", "content": f.read()}
        else:
            with open(path, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
                return {
                    "type": "binary", 
                    "content": encoded, 
                    "encoding": "base64",
                    "mimetype": guess_mimetype(path)
                }
    except OSError as e:
        raise OSError(f"Error reading file {file_path}: {e}")

@timed_operation("directory_scan")
def scan_directory(
    directory: PathLike, 
    limit: int, 
    filters: Optional[List[str]] = None
) -> List[str]:
    """
    Recursively scans a directory for files with performance optimizations.
    Uses glob matching if filters provided, otherwise finds text files.
    
    Args:
        directory: Directory to scan
        limit: Maximum number of files to return
        filters: Optional list of glob patterns to filter files
        
    Returns:
        List of file paths (up to limit)
        
    Raises:
        ValueError: If limit is not positive
        FileNotFoundError: If directory doesn't exist
    """
    if limit < 1:
        raise ValueError("limit must be positive")
    
    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    if not dir_path.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")
    
    found_files: List[str] = []
    perf_monitor.increment_counter("directories_scanned")
    
    if filters:
        # Use glob matching if filters are provided
        for filter_glob in filters:
            if len(found_files) >= limit:
                break
            
            # Create a recursive glob pattern
            search_pattern = str(dir_path / '**' / filter_glob)
            for file_path in glob.glob(search_pattern, recursive=True):
                if os.path.isfile(file_path):
                    found_files.append(file_path)
                    perf_monitor.increment_counter("files_found")
                    if len(found_files) >= limit:
                        break
    else:
        # Fallback to text file scanning
        for root, _, files in os.walk(str(dir_path)):
            if len(found_files) >= limit:
                break
            for file in files:
                file_path = os.path.join(root, file)
                if is_likely_text_file(file_path):
                    found_files.append(file_path)
                    perf_monitor.increment_counter("files_found")
                    if len(found_files) >= limit:
                        break
    
    logger.debug(f"Scanned directory '{directory}', found {len(found_files)} files")
    return found_files[:limit]

@timed_operation("file_validation")
def validate_file_path(file_path: PathLike) -> bool:
    """
    Validate that a file path exists and is accessible.
    
    Args:
        file_path: Path to validate
        
    Returns:
        True if path is valid and accessible, False otherwise
    """
    try:
        path = Path(file_path)
        return path.exists() and path.is_file()
    except (OSError, ValueError):
        return False

@timed_operation("directory_validation")
def validate_directory_path(dir_path: PathLike) -> bool:
    """
    Validate that a directory path exists and is accessible.
    
    Args:
        dir_path: Directory path to validate
        
    Returns:
        True if path is valid and accessible, False otherwise
    """
    try:
        path = Path(dir_path)
        return path.exists() and path.is_dir()
    except (OSError, ValueError):
        return False

def get_file_size(file_path: PathLike) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes, 0 if file doesn't exist or error occurs
    """
    try:
        return Path(file_path).stat().st_size
    except (OSError, ValueError):
        return 0

def ensure_directory_exists(dir_path: PathLike) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        dir_path: Directory path to ensure exists
        
    Returns:
        True if directory exists or was created successfully, False otherwise
    """
    try:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        return True
    except (OSError, ValueError):
        return False

def validate_file_size(file_path: PathLike, max_size_mb: int = 100) -> bool:
    """
    Validates that a file is not too large.
    
    Args:
        file_path: Path to the file
        max_size_mb: Maximum size in megabytes
        
    Returns:
        True if file size is acceptable, False otherwise
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return False
        
        size_mb = path.stat().st_size / (1024 * 1024)
        return size_mb <= max_size_mb
    except OSError:
        return False
    
def _extract_glob_list(pattern: str) -> list:
    """Extract comma-separated patterns from [pattern1,pattern2,...] format"""
    match = re.search(r'\[([^\]]+)\]', pattern)
    if match:
        return [p.strip() for p in match.group(1).split(',')]
    return [pattern]  # Return original if no brackets found

def resolve_glob(pattern: str) -> list:
    """Resolve custom glob pattern like './dir1/dir2/[*.py,Readme.md]'"""
    # Extract the bracket part
    bracket_match = re.search(r'^(.*?)\[([^\]]+)\](.*)$', pattern)
    
    if not bracket_match:
        # No brackets, treat as regular glob
        return glob.glob(pattern)
    
    prefix = bracket_match.group(1)  # './dir1/dir2/'
    suffix = bracket_match.group(3)  # usually empty
    
    # Get the list of patterns from brackets
    globs = _extract_glob_list(pattern)
    
    # Resolve each pattern
    all_files = []
    for glob_pattern in globs:
        full_pattern = f"{prefix}{glob_pattern}{suffix}"
        matches = glob.glob(full_pattern)
        all_files.extend(matches)
    
    return sorted(list(set(all_files)))  # Remove duplicates and sort