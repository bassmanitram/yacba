"""
Configuration orchestrator for YACBA.

This module serves as the unified entry point for all configuration parsing needs.
It handles:
- CLI argument parsing
- Configuration file loading (via profile-config with flexible overrides)
- Environment variable integration
- Tool discovery and validation
- Creating the final YacbaConfig object

The orchestrator uses profile-config 1.1's flexible overrides feature to handle
all configuration merging with proper precedence.
"""

import sys
import yaml
from pathlib import Path

from loguru import logger
from profile_config import ProfileConfigResolver
from profile_config.exceptions import ConfigNotFoundError, ProfileNotFoundError

from utils.general_utils import clean_dict
from yacba_types import ExitCode

from utils.config_utils import discover_tool_configs
from utils.file_utils import validate_file_path, get_file_size
from utils.model_config_parser import parse_model_config

from .arguments import (ARGUMENT_DEFAULTS, ARGUMENTS_FROM_ENV_VARS,
                        parse_args, validate_args)
from .dataclass import YacbaConfig

PROFILE_CONFIG_NAME = ".yacba"  # Config file base name
PROFILE_CONFIG_PROFILE_FILE_NAME = "config"  # Profile selection argument name

def _filter_cli_overrides(cli_args_dict):
    """
    Filter CLI arguments to only include those explicitly set by the user.
    
    Excludes:
    - None values (not provided)
    - False values for boolean flags (argparse defaults)
    - Empty lists (not provided)
    - Internal/meta arguments (list_profiles, show_config, init_config, profile, config_file)
    """
    # Arguments that are meta/control and shouldn't be in config
    meta_args = {'list_profiles', 'show_config', 'init_config', 'profile', 'config_file', 
                 'model_config', 'config_override', 'summarization_model_config', 'summarization_config_override'}
    
    filtered = {}
    for key, value in cli_args_dict.items():
        # Skip meta arguments
        if key in meta_args:
            continue
        
        # Skip None values
        if value is None:
            continue
        
        # Skip False boolean flags (these are argparse defaults, not user-provided)
        if isinstance(value, bool) and value is False:
            continue
        
        # Skip empty lists
        if isinstance(value, list) and len(value) == 0:
            continue
        
        # Include everything else
        filtered[key] = value
    
    return filtered


def parse_config() -> YacbaConfig:
    """
    Main configuration parsing entry point.
    
    Uses profile-config 1.1's flexible overrides to coordinate all configuration sources:
    1. Default values (lowest precedence)
    2. Environment variables
    3. Configuration files (with profiles via profile-config discovery)
    4. --config-file (user-specified override file)
    5. CLI arguments (highest precedence)
    
    Additionally handles:
    - Model configuration files (--model-config)
    - Tool discovery
    
    Returns:
        YacbaConfig: Fully validated configuration object
        
    Raises:
        SystemExit: On configuration errors
    """
    try:
        # 1. Parse CLI arguments first
        cli_args = parse_args()
        
        # Handle early-exit arguments
        if cli_args.list_profiles:
            try:
                resolver = ProfileConfigResolver(
                    config_name=PROFILE_CONFIG_NAME,
                    profile_filename=PROFILE_CONFIG_PROFILE_FILE_NAME,
                    extensions=["yaml", "yml"]
                )
                profiles = resolver.list_profiles()
                if profiles:
                    print("Available profiles:")
                    for profile in profiles:
                        print(f"  - {profile}")
                else:
                    print("No profiles found in configuration file.")
            except ConfigNotFoundError:
                print("No configuration file found. Expected at ./.yacba/config.yaml or ~/.yacba/config.yaml")
            sys.exit(0)
            
        if cli_args.init_config:
            output_path = Path(cli_args.init_config).expanduser().resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            sample_config = {
                'default_profile': 'development',
                'defaults': {
                    'conversation_manager': 'sliding_window',
                    'window_size': 40,
                    'max_files': 10
                },
                'profiles': {
                    'development': {
                        'model': 'litellm:gemini/gemini-1.5-flash',
                        'system_prompt': 'You are a helpful development assistant with access to tools.',
                        'tool_configs_dir': '~/.yacba/tools/',
                        'show_tool_use': True
                    },
                    'production': {
                        'model': 'openai:gpt-4',
                        'system_prompt': '@~/.yacba/prompts/production.txt',
                        'tool_configs_dir': '~/.yacba/tools/production/',
                        'show_tool_use': False,
                        'conversation_manager': 'summarizing',
                        'session': 'prod-session'
                    },
                    'coding': {
                        'inherits': 'development',
                        'model': 'anthropic:claude-3-sonnet',
                        'system_prompt': 'You are an expert programmer with access to development tools.',
                        'tool_configs_dir': '~/.yacba/tools/dev/',
                        'max_files': 50
                    }
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(sample_config, f, default_flow_style=False, indent=2)
            
            print(f"Sample configuration created at: {output_path}")
            print("Recommended locations:")
            print("  - ./.yacba/config.yaml (project-specific)")
            print("  - ~/.yacba/config.yaml (user-wide)")
            sys.exit(0)

        # 2. Build overrides list for profile-config (precedence order)
        overrides_list = []
        
        # Start with defaults (lowest precedence)
        overrides_list.append(ARGUMENT_DEFAULTS)
        logger.debug("Added ARGUMENT_DEFAULTS to overrides")
        
        # Add environment variables
        if ARGUMENTS_FROM_ENV_VARS:
            overrides_list.append(ARGUMENTS_FROM_ENV_VARS)
            logger.debug(f"Added {len(ARGUMENTS_FROM_ENV_VARS)} environment variables to overrides")
        
        # Add user-specified config file (NEW feature)
        if getattr(cli_args, 'config_file', None):
            overrides_list.append(cli_args.config_file)
            logger.info(f"Added config file override: {cli_args.config_file}")
        
        # Add CLI arguments (highest precedence) - only those explicitly set
        cli_overrides = _filter_cli_overrides(vars(cli_args))
        if cli_overrides:
            overrides_list.append(cli_overrides)
            logger.debug(f"Added {len(cli_overrides)} CLI arguments to overrides")

        # 3. Use profile-config with flexible overrides
        try:
            resolver = ProfileConfigResolver(
                config_name=PROFILE_CONFIG_NAME,
                profile_filename=PROFILE_CONFIG_PROFILE_FILE_NAME,
                profile=cli_args.profile or "default",
                extensions=["yaml", "yml"],
                search_home=True,
                overrides=overrides_list  # NEW: Use profile-config 1.1 flexible overrides
            )
            yacba_config = resolver.resolve()
            logger.info(f"Configuration resolved for profile '{cli_args.profile or 'default'}' with {len(overrides_list)} override sources")
        except ConfigNotFoundError:
            # No discovered files, but overrides still apply
            logger.debug("No configuration file found, using overrides only")
            # Create a minimal resolver with just overrides
            resolver = ProfileConfigResolver(
                config_name=PROFILE_CONFIG_NAME,
                profile_filename=PROFILE_CONFIG_PROFILE_FILE_NAME,
                profile="default",
                extensions=["yaml", "yml"],
                search_home=False,
                overrides=overrides_list
            )
            try:
                yacba_config = resolver.resolve()
            except ConfigNotFoundError:
                # Even with overrides, we need at least defaults
                logger.warning("No configuration sources available, using defaults only")
                yacba_config = ARGUMENT_DEFAULTS.copy()
        except ProfileNotFoundError as e:
            logger.error(f"Profile '{cli_args.profile}' not found in configuration")
            sys.exit(ExitCode.CONFIG_ERROR)
        
        # Validate the merged configuration
        yacba_config = validate_args(yacba_config)

        if cli_args.show_config:
            print("Resolved configuration:")
            for key, value in sorted(yacba_config.items()):
                print(f"  {key}: {repr(value)}")
            sys.exit(0)

        # 4. Parse model configuration if provided (separate from main config)
        model_config = {}
        model_config_file = getattr(cli_args, 'model_config', None)
        config_overrides = getattr(cli_args, 'config_override', None) or []
        
        if model_config_file:
            if not validate_file_path(model_config_file):
                logger.error(f"Model config file not found: {model_config_file}")
                sys.exit(ExitCode.CONFIG_ERROR)
            
            model_config_dict = parse_model_config(model_config_file, config_overrides)
            model_config.update(model_config_dict)

        # Parse summarization model configuration if provided (separate from main config)
        summarization_model_config = {}
        summarization_model_config_file = getattr(cli_args, 'summarization_model_config', None)
        summarization_config_overrides = getattr(cli_args, 'summarization_config_override', None) or []

        if summarization_model_config_file or summarization_config_overrides:
            if summarization_model_config_file and not validate_file_path(summarization_model_config_file):
                logger.error(f"Summarization model config file not found: {summarization_model_config_file}")
                sys.exit(ExitCode.CONFIG_ERROR)

            summarization_model_config_dict = parse_model_config(summarization_model_config_file, summarization_config_overrides)
            summarization_model_config.update(summarization_model_config_dict)
        # 5. Tool discovery and validation
        tool_configs = []
        tool_discovery_result = None
        
        if yacba_config.get('tool_configs_dir'):
            tool_configs, tool_discovery_result = discover_tool_configs(
                yacba_config.get('tool_configs_dir')
            )

        # 6. Process file uploads
        files_to_upload = []
        if yacba_config.get('files'):
            files_to_upload = yacba_config['files']

        # 7. Determine system prompt source for reporting
        prompt_source = "default"
        if yacba_config.get('system_prompt') != ARGUMENT_DEFAULTS.get('system_prompt'):
            if cli_overrides.get('system_prompt'):
                prompt_source = "command line"
            elif ARGUMENTS_FROM_ENV_VARS.get('system_prompt'):
                prompt_source = "environment"
            else:
                # Could be from discovered files or --config-file
                prompt_source = "configuration file"

        # 8. Create YacbaConfig from resolved configuration
        config = YacbaConfig(
            # Core required fields
            model_string=yacba_config.get('model'),
            system_prompt=yacba_config.get('system_prompt'),
            prompt_source=prompt_source,
            tool_config_paths=tool_configs,
            startup_files_content=None,  # Set later in lifecycle

            # Model configuration
            model_config=model_config,
            summarization_model_config=summarization_model_config,
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

            # Tool discovery results
            tool_discovery_result=tool_discovery_result
        )

        logger.debug("Configuration parsing completed using profile-config 1.1 flexible overrides")
        return config

    except Exception as e:
        logger.error(f"Configuration parsing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
