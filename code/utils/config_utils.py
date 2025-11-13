"""
Utility functions for configuration discovery and management.

Provides tool configuration discovery from *.tools.json files with
proper path expansion and error handling.
"""

import glob
from pathlib import Path
from typing import List, Union, Tuple

from utils.logging import get_logger

from yacba_types.config import ToolDiscoveryResult
from yacba_types.base import PathLike

logger = get_logger(__name__)


def discover_tool_configs(paths: Union[List[PathLike], PathLike, None]) -> Tuple[List[str], ToolDiscoveryResult]:
    """
    Discover tool configuration files from *.tools.json files.
    Returns absolute file paths for AgentFactory to process.

    Args:
        paths: Directory path(s) to search for tool configs, or None to disable discovery

    Returns:
        Tuple of (file_paths, discovery_result)
        - file_paths: List of absolute paths to *.tools.json files
        - discovery_result: Summary of discovery process
    """
    if paths is None:
        logger.info("tool_discovery_disabled")
        empty_result = ToolDiscoveryResult([], [], 0)
        return [], empty_result

    # Normalize to list
    if isinstance(paths, (str, Path)):
        path_list = [paths]
    else:
        path_list = list(paths)

    if not path_list:
        logger.info("no_tool_paths_provided")
        empty_result = ToolDiscoveryResult([], [], 0)
        return [], empty_result

    all_file_paths: List[str] = []
    all_failed_configs: List[dict] = []
    total_files_scanned = 0

    for directory in path_list:
        file_paths, failed_configs, files_scanned = _discover_single_directory(directory)
        all_file_paths.extend(file_paths)
        all_failed_configs.extend(failed_configs)
        total_files_scanned += files_scanned

    # Create discovery result with file paths as successful configs
    # (for backward compatibility with existing code that expects this structure)
    discovery_result = ToolDiscoveryResult(
        [{'file_path': path} for path in all_file_paths],  # Convert paths to dict format
        all_failed_configs,
        total_files_scanned
    )

    logger.info("tool_discovery_complete", 
                tool_count=len(all_file_paths), 
                directory_count=len(path_list))
    return all_file_paths, discovery_result


def _discover_single_directory(directory: PathLike) -> Tuple[List[str], List[dict], int]:
    """
    Discover tool configuration files from a single directory.

    Args:
        directory: Directory to search for tool configs

    Returns:
        Tuple of (file_paths, failed_configs, files_scanned)
    """
    # Expand ~ and resolve path
    dir_path = Path(directory).expanduser().resolve()
    
    if not dir_path.exists():
        logger.warning("tools_directory_not_found", directory=str(directory))
        return [], [], 0
    
    if not dir_path.is_dir():
        logger.warning("tools_path_not_directory", directory=str(directory))
        return [], [], 0

    search_pattern = str(dir_path / '*.tools.json')
    config_files = list(glob.glob(search_pattern))
    
    # Convert to absolute paths
    file_paths = [str(Path(f).absolute()) for f in config_files]
    
    logger.info("tool_configs_found", count=len(file_paths), directory=str(directory))
    
    # Log each found file
    for file_path in file_paths:
        logger.debug("tool_config_file_found", file_path=file_path)

    return file_paths, [], len(config_files)
