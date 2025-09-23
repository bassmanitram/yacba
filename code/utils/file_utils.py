from glob import glob
import mimetypes
import os
from pathlib import Path
from typing import List, Optional

from loguru import logger

from .performance_utils import timed_operation, perf_monitor
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
