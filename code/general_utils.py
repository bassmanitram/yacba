"""
Utility functions for YACBA .
Focused on YACBA's responsibilities:
- Configuration discovery and validation
- File system operations and content processing
- Path handling and validation
"""

import os
import json
import glob
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple

from loguru import logger
from yacba_types.config import ToolConfig
from yacba_types.models import FrameworkName
from performance_utils import cached_operation, timed_operation, perf_monitor

# Type alias for path-like objects
PathLike = Union[str, Path]

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

@cached_operation("tool_discovery")
def discover_tool_configs(directory: Optional[PathLike]) -> List[ToolConfig]:
    """
    Discovers and loads tool configurations from *.tools.json files with caching.
    YACBA only validates the configuration structure, not tool functionality.
    
    Args:
        directory: Directory to search for tool configs, None to disable discovery
        
    Returns:
        List of validated tool configurations
    """
    if directory is None:
        logger.info("Tool discovery is disabled by command-line option.")
        return []
    
    dir_path = Path(directory)
    if not dir_path.exists():
        logger.warning(f"Tools directory not found: '{directory}'. Skipping tool discovery.")
        return []
    if not dir_path.is_dir():
        logger.warning(f"Tools path is not a directory: '{directory}'. Skipping tool discovery.")
        return []

    configs: List[ToolConfig] = []
    search_pattern = str(dir_path / '*.tools.json')
    
    perf_monitor.increment_counter("tool_discovery_attempts")
    
    for file_path in glob.glob(search_pattern):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # Add source file reference for debugging
            config_data['source_file'] = file_path
            
            # Basic configuration validation (structure only)
            if not _validate_tool_config_structure(config_data):
                logger.warning(f"Invalid tool config structure in '{file_path}'. Skipping.")
                perf_monitor.increment_counter("invalid_tool_configs")
                continue
                
            configs.append(config_data)
            perf_monitor.increment_counter("valid_tool_configs")
            logger.debug(f"Loaded tool config: {config_data.get('id', 'unknown')} from {file_path}")
            
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load or parse tool config '{file_path}': {e}")
            perf_monitor.increment_counter("tool_config_errors")
        except Exception as e:
            logger.error(f"Unexpected error loading tool config '{file_path}': {e}")
            perf_monitor.increment_counter("tool_config_errors")
    
    logger.info(f"Discovered {len(configs)} tool configurations")
    return configs

def _validate_tool_config_structure(config: Dict[str, Any]) -> bool:
    """
    Validates a tool configuration dictionary structure.
    YACBA only checks configuration format, not tool functionality.
    
    Args:
        config: Tool configuration to validate
        
    Returns:
        True if structure is valid, False otherwise
    """
    # Required fields
    if 'id' not in config:
        return False
    
    if 'type' not in config:
        return False
    
    # Type-specific validation
    config_type = config.get('type')
    
    if config_type == 'mcp-stdio':
        # MCP stdio requires command
        if 'command' not in config:
            return False
    elif config_type == 'mcp-http':
        # MCP HTTP requires url
        if 'url' not in config:
            return False
    elif config_type == 'python-module':
        # Python module requires module path
        if 'module' not in config:
            return False
    
    return True

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

# Framework guessing rules with type safety
FRAMEWORK_GUESSING_RULES: List[Tuple[str, FrameworkName]] = [
    ("gpt-", "openai"),
    ("claude", "anthropic"),
    ("gemini", "litellm"),
    ("google", "litellm"),
    ("/", "litellm"),  # Convention for litellm models like 'ollama/llama2'
]

def guess_framework_from_model_string(model_name: str) -> FrameworkName:
    """
    Makes a best guess for the model framework based on a list of rules.
    
    Args:
        model_name: The model name to analyze
        
    Returns:
        The guessed framework name
    """
    if not model_name:
        logger.warning("Empty model name provided. Defaulting to 'litellm'.")
        return "litellm"
    
    model_lower = model_name.lower()
    for condition, framework in FRAMEWORK_GUESSING_RULES:
        if condition in model_lower:
            logger.debug(f"Guessed '{framework}' framework for model '{model_name}' based on rule '{condition}'.")
            return framework
    
    # Default fallback if no rules match
    logger.warning(f"Could not determine framework for '{model_name}' based on rules. Defaulting to 'litellm'.")
    return "litellm"

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
