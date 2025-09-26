"""
Configuration parsing and validation for YACBA.

This module handles command-line argument parsing, environment variable processing,
and configuration validation. It provides a single entry point for all configuration
needs through the parse_config() function.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple

from loguru import logger

# Import utilities
from utils.file_utils import (
    guess_mimetype,
    validate_file_path,
    validate_directory_path,
    get_file_size,
    is_likely_text_file,
    ensure_directory_exists,
    validate_file_size
)
from utils.content_processing import process_path_argument
from utils.config_discovery import discover_tool_configs
from yacba_types.config import ModelConfig, ToolConfig, FileUpload, ToolDiscoveryResult
from yacba_types.base import PathLike
from .config import YacbaConfig

# Define constants for clarity and maintainability.
DEFAULT_MODEL = "litellm:gemini/gemini-2.5-flash"
DEFAULT_SYSTEM_PROMPT = "You are a general assistant with access to various tools to enhance your capabilities. You are NOT a specialized assistant dedicated to any specific tool provider."
DEFAULT_MAX_FILES = 10
DEFAULT_SESSION_NAME = "default"

def _get_default_model() -> str:
    """Get the default model from environment or constant."""
    return os.environ.get("YACBA_MODEL_ID", DEFAULT_MODEL)

def _get_default_system_prompt() -> str:
    """Get the default system prompt from environment or constant."""
    return os.environ.get("YACBA_SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT)

def _get_default_session_name() -> str:
    """Get the default session name from environment or constant."""
    return os.environ.get("YACBA_SESSION_NAME", DEFAULT_SESSION_NAME)

def _validate_model_string(model_string: str) -> None:
    """
    Validate the model string format.
    
    Args:
        model_string: The model string to validate
        
    Raises:
        ValueError: If the model string format is invalid
    """
    if not model_string:
        raise ValueError("Model string cannot be empty")
    
    # Basic validation - should contain framework:model format
    if ":" not in model_string:
        raise ValueError(f"Model string '{model_string}' must be in format 'framework:model'")

def _process_file_uploads(file_paths: List[str]) -> List[FileUpload]:
    """
    Process file upload paths and create FileUpload objects.
    
    Args:
        file_paths: List of file paths to process
        
    Returns:
        List of FileUpload objects
        
    Raises:
        FileNotFoundError: If a file doesn't exist
        ValueError: If a file is not readable
    """
    uploads = []
    
    for path_str in file_paths:
        try:
            # Validate the path
            path = Path(path_str).resolve()
            if not validate_file_path(path):
                raise FileNotFoundError(f"File not found or not accessible: {path_str}")
            
            # Get file information
            mimetype = guess_mimetype(path)
            size = get_file_size(path)
            
            # Create FileUpload object
            upload = FileUpload(
                path=str(path),
                mimetype=mimetype,
                size=size
            )
            uploads.append(upload)
            
        except Exception as e:
            logger.error(f"Error processing file '{path_str}': {e}")
            raise
    
    return uploads

def _create_model_config(model_string: str, **kwargs) -> ModelConfig:
    """
    Create a ModelConfig object from the model string and additional parameters.
    
    Args:
        model_string: The model string in format 'framework:model'
        **kwargs: Additional model configuration parameters
        
    Returns:
        ModelConfig object
    """
    # Parse framework and model from string
    if ":" in model_string:
        framework, model_id = model_string.split(":", 1)
    else:
        # Fallback for legacy format
        framework = "litellm"
        model_id = model_string
    
    return ModelConfig(
        framework=framework,
        model_id=model_id,
        **kwargs
    )

def _setup_argument_parser() -> argparse.ArgumentParser:
    """
    Set up and configure the argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    default_model = _get_default_model()
    
    parser = argparse.ArgumentParser(
        description="Yet Another ChatBot Agent - A flexible AI assistant with tool integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  yacba                                    # Interactive mode with default model
  yacba -m openai:gpt-4                   # Use specific model
  yacba -t ./tools/                       # Load tools from directory
  yacba -i "Hello, world!" --headless     # Headless mode with message
  yacba -f document.pdf -i "Analyze this" # Upload file and analyze
  yacba --session my-session              # Use named session
  
Environment Variables:
  YACBA_MODEL_ID      Default model (default: {default_model})
  YACBA_SYSTEM_PROMPT Default system prompt
  YACBA_SESSION_NAME  Default session name
  LOGURU_LEVEL        Logging level (DEBUG, INFO, WARNING, ERROR)
        """
    )
    
    # Model configuration
    parser.add_argument(
        "-m", "--model",
        default=default_model,
        help=f"The model to use, in <framework>:<model_id> format. Default: {default_model} (or from YACBA_MODEL_ID)."
    )
    
    # System prompt
    parser.add_argument(
        "-s", "--system-prompt",
        default=_get_default_system_prompt(),
        help="System prompt for the agent. Can also be set via YACBA_SYSTEM_PROMPT."
    )
    
    parser.add_argument(
        "--emulate-system-prompt",
        action="store_true",
        help="Emulate system prompt as user message for models that don't support system prompts."
    )
    
    # Tool configuration
    parser.add_argument(
        "-t", "--tool-configs",
        nargs="*",
        default=[],
        help="Paths to tool configuration files or directories. Can be specified multiple times."
    )
    
    # File uploads
    parser.add_argument(
        "-f", "--files",
        nargs="*",
        default=[],
        help="Files to upload and analyze. Can be specified multiple times."
    )
    
    parser.add_argument(
        "--max-files",
        type=int,
        default=DEFAULT_MAX_FILES,
        help=f"Maximum number of files to process. Default: {DEFAULT_MAX_FILES}."
    )
    
    # Session management
    parser.add_argument(
        "--session",
        default=_get_default_session_name(),
        help=f"Session name for conversation persistence. Default: {_get_default_session_name()} (or from YACBA_SESSION_NAME)."
    )
    
    # Execution modes
    parser.add_argument(
        "-i", "--initial-message",
        help="Initial message to send to the agent."
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (non-interactive). Requires --initial-message."
    )
    
    # Output control
    parser.add_argument(
        "--show-tool-use",
        action="store_true",
        help="Show detailed tool usage information during execution."
    )
    
    parser.add_argument(
        "--agent-id",
        help="Custom agent identifier for this session."
    )
    
    # Performance and debugging
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear the performance cache before starting."
    )
    
    return parser

def _validate_configuration(config: YacbaConfig) -> None:
    """
    Validate the complete configuration for consistency and requirements.
    
    Args:
        config: The configuration to validate
        
    Raises:
        ValueError: If configuration is invalid
    """
    # Validate model string
    _validate_model_string(config.model_string)
    
    # Validate headless mode requirements
    if config.headless and not config.initial_message:
        raise ValueError("Headless mode requires an initial message via --initial-message")
    
    # Validate file limits
    if len(config.files_to_upload) > config.max_files:
        raise ValueError(f"Too many files specified ({len(config.files_to_upload)}). Maximum allowed: {config.max_files}")
    
    # Validate session name
    if not config.session_name or not config.session_name.strip():
        raise ValueError("Session name cannot be empty")

def parse_config() -> YacbaConfig:
    """
    Parse command-line arguments and environment variables to create a YacbaConfig.
    
    This is the main entry point for configuration parsing. It handles:
    - Command-line argument parsing
    - Environment variable processing
    - File upload processing
    - Tool configuration discovery
    - Configuration validation
    
    Returns:
        Fully configured YacbaConfig instance
        
    Raises:
        SystemExit: On configuration errors or validation failures
    """
    try:
        # Parse command-line arguments
        parser = _setup_argument_parser()
        args = parser.parse_args()
        
        # Process file uploads
        files_to_upload = []
        if args.files:
            try:
                files_to_upload = _process_file_uploads(args.files)
                logger.info(f"Processed {len(files_to_upload)} file uploads")
            except Exception as e:
                logger.error(f"Error processing file uploads: {e}")
                sys.exit(1)
        
        # Discover and process tool configurations
        tool_configs = []
        tool_discovery_result = ToolDiscoveryResult([], [], 0)  # Default empty result
        if args.tool_configs:
            try:
                tool_configs, tool_discovery_result = discover_tool_configs(args.tool_configs)
                logger.info(f"Discovered {len(tool_configs)} tool configurations")
            except Exception as e:
                logger.error(f"Error discovering tool configurations: {e}")
                sys.exit(1)
        
        # Create model configuration
        model_config = _create_model_config(args.model)
        
        # Determine prompt source for display
        prompt_source = "environment" if os.environ.get("YACBA_SYSTEM_PROMPT") else "default"
        if args.system_prompt != _get_default_system_prompt():
            prompt_source = "command-line"
        
        # Create the main configuration
        config = YacbaConfig(
            # Model configuration
            model_string=args.model,
            model_config=model_config,
            system_prompt=args.system_prompt,
            prompt_source=prompt_source,
            emulate_system_prompt=args.emulate_system_prompt,
            
            # Tool configuration
            tool_configs=tool_configs,
            tool_discovery_result=tool_discovery_result,
            
            # File handling
            files_to_upload=files_to_upload,
            max_files=args.max_files,
            
            # Session management
            session_name=args.session,
            agent_id=args.agent_id,
            
            # Execution mode
            headless=args.headless,
            initial_message=args.initial_message,
            
            # Output control
            show_tool_use=args.show_tool_use,
            
            # Will be set later by main application
            startup_files_content=None
        )
        
        # Validate the complete configuration
        _validate_configuration(config)
        
        logger.debug("Configuration parsing completed successfully")
        return config
        
    except Exception as e:
        logger.error(f"Configuration parsing failed: {e}")
        sys.exit(1)

# Convenience functions for specific configuration aspects
def get_model_config(model_string: str) -> ModelConfig:
    """
    Create a ModelConfig from a model string.
    
    Args:
        model_string: Model string in format 'framework:model'
        
    Returns:
        ModelConfig instance
    """
    return _create_model_config(model_string)

def validate_file_upload(file_path: str) -> FileUpload:
    """
    Validate and create a FileUpload for a single file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        FileUpload instance
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is not readable
    """
    uploads = _process_file_uploads([file_path])
    return uploads[0]