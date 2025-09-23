import glob
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from yacba_types.tools import ToolConfig
from yacba_types.config import ToolDiscoveryResult
from yacba_types.base import PathLike
from .performance_utils import cached_operation, perf_monitor

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
