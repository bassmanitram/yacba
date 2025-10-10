"""
Configuration orchestrator for YACBA.

This module serves as the unified entry point for all configuration parsing needs.
It handles:
- CLI argument parsing
- Configuration file loading
- Environment variable integration
- Tool discovery and validation
- Creating the final YacbaConfig object

The orchestrator coordinates between the various configuration sources and
ensures a consistent configuration object is provided to the application.
"""

import sys

from loguru import logger

from utils.general_utils import clean_dict
from yacba_types import ExitCode

from utils.config_discovery import discover_tool_configs
from utils.file_utils import validate_file_path, get_file_size
from utils.model_config_parser import parse_model_config

from .arguments import (ARGUMENT_DEFAULTS, ARGUMENTS_FROM_ENV_VARS,
                        parse_args, validate_args)
from .file_loader import ConfigManager
from .dataclass import YacbaConfig


def parse_config() -> YacbaConfig:
    """
    Main configuration parsing entry point.
    
    Coordinates all configuration sources:
    1. Default values
    2. Environment variables
    3. Configuration files (with profiles)
    4. CLI arguments
    5. Model configuration files
    6. Tool discovery
    
    Returns:
        YacbaConfig: Fully validated configuration object
        
    Raises:
        SystemExit: On configuration errors
    """
    try:
        # 1. Parse CLI arguments first to get config file paths and profile
        cli_args = parse_args()
        
        # Handle early-exit arguments
        config_manager = ConfigManager()
        
        if cli_args.list_profiles:
            if cli_args.config:
                # Need to load the config file first to list profiles
                config_manager.load_config(config_file=cli_args.config)
                profiles = config_manager.list_profiles()
                if profiles:
                    print("Available profiles:")
                    for profile in profiles:
                        print(f"  - {profile}")
                else:
                    print("No profiles found in configuration file.")
            else:
                print("No configuration file specified. Use --config to specify a file.")
            sys.exit(0)
            
        if cli_args.init_config:
            config_manager.create_sample_config(cli_args.init_config)
            print(f"Sample configuration created at: {cli_args.init_config}")
            sys.exit(0)

        # 2. Parse model configuration if provided
        model_config = {}
        model_config_file = getattr(cli_args, 'model_config', None)
        config_overrides = getattr(cli_args, 'config_override', None) or []
        
        if model_config_file:
            if not validate_file_path(model_config_file):
                logger.error(f"Model config file not found: {model_config_file}")
                sys.exit(ExitCode.CONFIG_ERROR)
            
            # Check file size (reasonable limit)
            size = get_file_size(model_config_file)
            if size > 1024 * 1024:  # 1MB limit
                logger.error(f"Model config file too large: {size} bytes")
                sys.exit(ExitCode.CONFIG_ERROR)
                
            model_config_dict = parse_model_config(model_config_file,
                                                   config_overrides)
            model_config.update(model_config_dict)

        # 3. Load configuration from files
        config_from_files = {}
        if cli_args.config:
            config_manager.load_config(config_file=cli_args.config)
            config_from_files = config_manager.get_resolved_config(profile=cli_args.profile)
        
        config_from_args = vars(cli_args)
        
        # Merge in priority order: defaults -> env vars -> files -> args
        yacba_config = {**ARGUMENT_DEFAULTS,
                        **ARGUMENTS_FROM_ENV_VARS,
                        **config_from_files, 
                        **clean_dict(config_from_args)}
        
        # Validate the merged configuration
        yacba_config = validate_args(yacba_config)

        if cli_args.show_config:
            print("Resolved configuration:")
            for key, value in sorted(yacba_config.items()):
                print(f"  {key}: {repr(value)}")
            sys.exit(0)

        # 4. Tool discovery and validation
        tool_configs = []
        tool_discovery_result = None
        
        if yacba_config.get('tool_configs_dir'):
            tool_configs, tool_discovery_result = discover_tool_configs(
                yacba_config.get('tool_configs_dir')
            )

        # 5. Process file uploads
        files_to_upload = []
        if yacba_config.get('files'):
            files_to_upload = yacba_config['files']

        # 6. Determine system prompt source for reporting
        prompt_source = "default"
        if yacba_config.get('system_prompt') != ARGUMENT_DEFAULTS.get('system_prompt'):
            if config_from_args.get('system_prompt'):
                prompt_source = "command line"
            elif config_from_files.get('system_prompt'):
                prompt_source = "configuration file"
            elif ARGUMENTS_FROM_ENV_VARS.get('system_prompt'):
                prompt_source = "environment"

        # 7. Create YacbaConfig directly from merged configuration
        config = YacbaConfig(
            # Core required fields
            model_string=yacba_config.get('model'),
            system_prompt=yacba_config.get('system_prompt'),
            prompt_source=prompt_source,
            tool_config_paths=tool_configs,
            startup_files_content=None,  # Set later in lifecycle

            # Model configuration
            model_config=model_config,
            emulate_system_prompt=yacba_config.get('emulate_system_prompt', False),

            # File handling
            files_to_upload=files_to_upload,
            max_files=yacba_config.get('max_files', 20),

            # Session management
            session_name=yacba_config.get('session'),
            agent_id=yacba_config.get('agent_id'),

            # Conversation management
            conversation_manager_type=yacba_config.get('conversation_manager', 'sliding_window'),
            sliding_window_size=yacba_config.get('window_size', 40),
            preserve_recent_messages=yacba_config.get('preserve_recent', 10),
            summary_ratio=yacba_config.get('summary_ratio', 0.3),
            summarization_model=yacba_config.get('summarization_model'),
            custom_summarization_prompt=yacba_config.get('custom_summarization_prompt'),
            should_truncate_results=not yacba_config.get('no_truncate_results', False),

            # Execution mode
            headless=yacba_config.get('headless', False),
            initial_message=yacba_config.get('initial_message'),

            # Output control
            show_tool_use=yacba_config.get('show_tool_use', False),
            # User interface customization
            cli_prompt=yacba_config.get('cli_prompt'),
            response_prefix=yacba_config.get('response_prefix'),

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