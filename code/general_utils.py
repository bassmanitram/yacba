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
from yacba_types.config import ToolConfig, ToolDiscoveryResult  # Import from types
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
def discover_tool_configs(directory: Optional[PathLike]) -> ToolDiscoveryResult:
    """
    Enhanced discovery with detailed error reporting.
    Discovers and loads tool configurations from *.tools.json files with caching.
    YACBA only validates the configuration structure, not tool functionality.
    
    Args:
        directory: Directory to search for tool configs, None to disable discovery
        
    Returns:
        ToolDiscoveryResult with successful configs, failed configs, and scan count
    """
    if directory is None:
        logger.info("Tool discovery is disabled by command-line option.")
        return ToolDiscoveryResult([], [], 0)
    
    dir_path = Path(directory)
    if not dir_path.exists():
        logger.warning(f"Tools directory not found: '{directory}'. Skipping tool discovery.")
        return ToolDiscoveryResult([], [], 0)
    if not dir_path.is_dir():
        logger.warning(f"Tools path is not a directory: '{directory}'. Skipping tool discovery.")
        return ToolDiscoveryResult([], [], 0)

    successful_configs: List[ToolConfig] = []
    failed_configs: List[Dict[str, Any]] = []
    search_pattern = str(dir_path / '*.tools.json')
    config_files = list(glob.glob(search_pattern))
    
    perf_monitor.increment_counter("tool_discovery_attempts")
    logger.info(f"Scanning {len(config_files)} tool configuration files in '{directory}'")
    
    for file_path in config_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # Add source file reference for debugging
            config_data['source_file'] = file_path
            
            # Enhanced validation with detailed error messages
            validation_errors = _validate_tool_config_detailed(config_data)
            if not validation_errors:
                successful_configs.append(config_data)
                perf_monitor.increment_counter("valid_tool_configs")
                logger.info(f"✓ Loaded tool config '{config_data.get('id', 'unknown')}' from {file_path}")
            else:
                error_msg = f"Invalid configuration: {'; '.join(validation_errors)}"
                failed_configs.append({
                    'file_path': file_path,
                    'config_id': config_data.get('id', 'unknown'),
                    'error': error_msg,
                    'config_data': config_data
                })
                perf_monitor.increment_counter("invalid_tool_configs")
                logger.warning(f"✗ Failed to load tool config from {file_path}: {error_msg}")
                
        except json.JSONDecodeError as e:
            error_msg = f"JSON parsing error: {e}"
            failed_configs.append({
                'file_path': file_path,
                'config_id': 'unknown',
                'error': error_msg,
                'config_data': None
            })
            perf_monitor.increment_counter("tool_config_errors")
            logger.error(f"✗ Failed to parse {file_path}: {error_msg}")
        except IOError as e:
            error_msg = f"File read error: {e}"
            failed_configs.append({
                'file_path': file_path,
                'config_id': 'unknown', 
                'error': error_msg,
                'config_data': None
            })
            perf_monitor.increment_counter("tool_config_errors")
            logger.error(f"✗ Failed to read {file_path}: {error_msg}")
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            failed_configs.append({
                'file_path': file_path,
                'config_id': 'unknown',
                'error': error_msg,
                'config_data': None
            })
            perf_monitor.increment_counter("tool_config_errors")
            logger.error(f"✗ Unexpected error loading tool config '{file_path}': {error_msg}")
    
    logger.info(f"Tool discovery complete: {len(successful_configs)} successful, {len(failed_configs)} failed")
    return ToolDiscoveryResult(successful_configs, failed_configs, len(config_files))

def _validate_tool_config_detailed(config: Dict[str, Any]) -> List[str]:
    """
    Enhanced validation with detailed error messages.
    Validates a tool configuration dictionary structure.
    YACBA only checks configuration format, not tool functionality.
    
    Args:
        config: Tool configuration to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Validate required fields
    if 'id' not in config:
        errors.append("missing required field 'id'")
    elif not isinstance(config['id'], str) or not config['id'].strip():
        errors.append("'id' must be a non-empty string")
    
    if 'type' not in config:
        errors.append("missing required field 'type'")
    else:
        config_type = config.get('type')
        
        # Type-specific validation
        if config_type == 'mcp':
            if 'command' not in config and 'url' not in config:
                errors.append("MCP tools require either 'command' (stdio) or 'url' (http)")
            if 'command' in config and 'url' in config:
                errors.append("MCP tools cannot have both 'command' and 'url'")
            
            # Validate command structure if present
            if 'command' in config:
                if not isinstance(config['command'], str) or not config['command'].strip():
                    errors.append("'command' must be a non-empty string")
                if 'args' in config and not isinstance(config['args'], list):
                    errors.append("'args' must be a list")
                if 'env' in config and not isinstance(config['env'], dict):
                    errors.append("'env' must be a dictionary")
            
            # Validate URL structure if present
            if 'url' in config:
                if not isinstance(config['url'], str) or not config['url'].strip():
                    errors.append("'url' must be a non-empty string")
                # Basic URL format check
                url = config['url']
                if not (url.startswith('http://') or url.startswith('https://')):
                    errors.append("'url' must start with 'http://' or 'https://'")
                    
        elif config_type == 'python':
            if 'module_path' not in config:
                errors.append("Python tools require 'module_path'")
            elif not isinstance(config['module_path'], str) or not config['module_path'].strip():
                errors.append("'module_path' must be a non-empty string")
                
            if 'functions' not in config:
                errors.append("Python tools require 'functions' list")
            elif not isinstance(config.get('functions'), list):
                errors.append("'functions' must be a list")
            elif not config['functions']:
                errors.append("'functions' list cannot be empty")
            else:
                # Validate function names
                for i, func_name in enumerate(config['functions']):
                    if not isinstance(func_name, str) or not func_name.strip():
                        errors.append(f"function name at index {i} must be a non-empty string")
        else:
            errors.append(f"unknown tool type '{config_type}' (supported: 'mcp', 'python')")
    
    # Validate optional disabled field
    if 'disabled' in config and not isinstance(config['disabled'], bool):
        errors.append("'disabled' must be a boolean")
    
    return errors

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
