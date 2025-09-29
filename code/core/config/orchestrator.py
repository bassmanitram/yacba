"""
Streamlined configuration orchestrator for YACBA.

This eliminates double-parsing by integrating configuration file resolution
directly with argument parsing. The flow is now:
1. Discover and load configuration files
2. Merge config values with CLI arguments in a single pass
3. Create YacbaConfig directly from merged configuration
4. Handle special commands (--list-profiles, etc.)

This maintains backward compatibility while providing much better performance.
"""

import sys
from typing import Any, Dict, Optional, List
from pathlib import Path
from loguru import logger

from .file_loader import ConfigManager
from .argument_definitions import (ARGUMENT_DEFAULTS, ARGUMENTS_FROM_ENV_VARS,
                                   parse_args, validate_args)
from .dataclass import YacbaConfig
from utils.config_discovery import discover_tool_configs
from utils.file_utils import validate_file_path, get_file_size
from utils.model_config_parser import parse_model_config, ModelConfigError
from yacba_types.config import ToolDiscoveryResult, FileUpload


def _process_file_uploads(file_paths: List[str]) -> List[FileUpload]:
    """
    Process file upload paths and create FileUpload objects.

    Args:
        file_path, mimetype pairs

    Returns:
        List of FileUpload objects

    Raises:
        FileNotFoundError: If a file doesn't exist
        ValueError: If a file is not readable
    """
    uploads = []

    for path_str, mimetype in file_paths:
        try:
            # Validate the path
            path = Path(path_str).resolve()
            if not validate_file_path(path):
                raise FileNotFoundError(
                    f"File not found or not accessible: {path_str}")

            # Get file information
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


def _create_model_config(
        model_config_file: Optional[str] = None,
        model_config_overrides: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    # Parse model configuration from file and overrides
    Args:
        model_config_file: Optional path to model config file
        model_config_overrides: Optional list of key=value overrides
    Returns:
        Parsed model configuration dictionary
    Raises:
        ValueError: If parsing fails
    """

    try:
        model_config_dict = parse_model_config(model_config_file,
                                                model_config_overrides)
        logger.debug(f"Parsed model config: {len(model_config_dict)} "
                     "properties")
    except ModelConfigError as e:
        logger.error(f"Model configuration error: {e}")
        raise ValueError(f"Model configuration error: {e}")

    # Create ModelConfig with all the configuration

    return model_config_dict


def parse_config() -> YacbaConfig:
    """
    Parse configuration using integrated config file + CLI approach.

    This eliminates double parsing by:
    1. Handling special commands first (--list-profiles, etc.)
    2. Loading configuration files if specified
    3. Parsing CLI arguments once
    4. Merging config + CLI in single pass
    5. Creating YacbaConfig directly

    Returns:
        Fully resolved YacbaConfig instance

    Raises:
        SystemExit: For special commands or configuration errors
    """
    try:
        # Create integrated parser
        config_from_args = parse_args()
        logger.debug(f"Parsed CLI arguments: {config_from_args}")

        # Load configuration files if specified
        config_manager = ConfigManager()

        # Handle special commands that exit immediately
        if config_from_args.list_profiles:
            profiles = config_manager.list_profiles()
            if profiles:
                print("Available profiles:")
                for profile in profiles:
                    print(f"  - {profile}")
            else:
                print("No profiles found in configuration file.")
            sys.exit(0)

        if config_from_args.init_config:
            config_manager.create_sample_config(config_from_args.init_config)
            print("Configuration file created at: "
                  f"{config_from_args.init_config}")
            sys.exit(0)

        config_from_files = config_manager.load_config(
            config_path=config_from_args.config,
            profile=config_from_args.profile
        )

        # Merge configurations: defaults < env vars < config files < CLI args
        # Later sources override earlier ones
        # Start with defaults
        yacba_config = (ARGUMENT_DEFAULTS | ARGUMENTS_FROM_ENV_VARS |
                        config_from_files | vars(config_from_args))
        # We need to tweak a couple though
        yacba_config['files'] = (
            (ARGUMENT_DEFAULTS.get('files') or []) +
            (ARGUMENTS_FROM_ENV_VARS.get('files') or []) +
            (config_from_files.get('files') or []) +
            (config_from_args.files or []))
        yacba_config['config_override'] = (
            (ARGUMENT_DEFAULTS.get('config_override') or []) +
            (ARGUMENTS_FROM_ENV_VARS.get('config_override') or []) +
            (config_from_files.get('config_override') or []) +
            (config_from_args.config_override or []))

        if yacba_config.get("show_config"):
            # Show merged configuration and exit
            merged = yacba_config
            import yaml
            print("Resolved configuration:")
            print(yaml.dump(merged, default_flow_style=False))
            sys.exit(0)

        logger.debug(f"Merged configuration: {yacba_config}")

        # Validate merged configuration
        yacba_config = validate_args(yacba_config)

        # 1. Process file uploads
        files_to_upload = []
        files_list = yacba_config.get('files')
        if (files_list and isinstance(files_list, list) and
                len(files_list) > 0):
            files_to_upload = _process_file_uploads(files_list)
            logger.info(f"Processed {len(files_to_upload)} file uploads")

        # 2. Discover and process tool configurations
        tool_configs = []
        tool_discovery_result = ToolDiscoveryResult([], [], 0)
        tool_configs_dir = yacba_config.get('tool_configs_dir')
        # Now handle single directory path (string) instead of list
        if (tool_configs_dir and isinstance(tool_configs_dir, str) and
                tool_configs_dir.strip()):
            tool_configs, tool_discovery_result = discover_tool_configs(
                tool_configs_dir)
            logger.info(f"Discovered {len(tool_configs)} tool "
                        f"configurations from directory: {tool_configs_dir}")

        # 3. Create model configuration
        model_config = _create_model_config(
            yacba_config.get('model_config'),
            yacba_config.get('config_override')
        )

        # 4. Determine system prompt source
        prompt_source = "default"
        if config_from_args.system_prompt:
            prompt_source = "command-line"
        elif config_from_files.get('system_prompt'):
            prompt_source = "config-file"
        elif ARGUMENTS_FROM_ENV_VARS.get('system_prompt'):
            prompt_source = "environment"

        # 5. Validate configuration before creating YacbaConfig
        # Create YacbaConfig directly from merged configuration
        config = YacbaConfig(
            # Core required fields
            model_string=yacba_config.get('model'),
            system_prompt=yacba_config.get('system_prompt'),
            prompt_source=prompt_source,
            tool_configs=tool_configs,
            startup_files_content=None,  # Set later in lifecycle

            # Model configuration
            model_config=model_config,
            emulate_system_prompt=yacba_config.get('emulate_system_prompt'),

            # File handling
            files_to_upload=files_to_upload,
            max_files=yacba_config.get('max_files'),

            # Session management
            session_name=yacba_config.get('session'),
            agent_id=yacba_config.get('agent_id'),

            # Conversation management
            conversation_manager_type=yacba_config.get('conversation_manager',
                                                       'sliding_window'),
            sliding_window_size=yacba_config.get('window_size', 40),
            preserve_recent_messages=yacba_config.get('preserve_recent', 10),
            summary_ratio=yacba_config.get('summary_ratio', 0.3),
            summarization_model=yacba_config.get('summarization_model'),
            custom_summarization_prompt=yacba_config.get(
                'custom_summarization_prompt'),
            should_truncate_results=not yacba_config.get(
                    'no_truncate_results', False),

            # Execution mode
            headless=yacba_config.get('headless', False),
            initial_message=yacba_config.get('initial_message'),

            # Output control
            show_tool_use=yacba_config.get('show_tool_use', False),

            # Performance
            clear_cache=yacba_config.get('clear_cache', False),
            show_perf_stats=yacba_config.get('show_perf_stats', False),
            disable_cache=yacba_config.get('disable_cache', False),

            # Tool discovery results (set during parsing)
            tool_discovery_result=tool_discovery_result
        )

        logger.debug("Configuration parsing completed via integrated system")
        return config

    except Exception as e:
        logger.error(f"Configuration parsing failed: {e}")
        sys.exit(1)


# Backward compatibility


def orchestrate_config_parsing() -> YacbaConfig:
    """Backward compatibility wrapper."""
    return parse_config()
