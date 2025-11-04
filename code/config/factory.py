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

dataclass-args now handles model_config and summarization_model_config as dict fields
with automatic file loading and property overrides (--model-config file.json --mc key:value).
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
from utils.file_utils import validate_file_path

from .arguments import (ARGUMENT_DEFAULTS, ARGUMENTS_FROM_ENV_VARS,
                        parse_args, validate_args)
from .dataclass import YacbaConfig

PROFILE_CONFIG_NAME = ".yacba"  # Config file base name
PROFILE_CONFIG_PROFILE_FILE_NAME = "config"  # Profile selection argument name

def _normalize_cli_field_names(cli_args_dict):
    """
    Normalize CLI field names to match profile-config field names.
    
    CLI uses dataclass field names (e.g., model_string, session_name)
    profile-config uses shorter names (e.g., model, session)
    
    This function creates a normalized dict with both naming conventions.
    """
    normalized = cli_args_dict.copy()
    
    # Add aliases for fields where CLI name differs from profile-config name
    field_name_mappings = {
        'model_string': 'model',
        'session_name': 'session',
        'conversation_manager_type': 'conversation_manager',
        'sliding_window_size': 'window_size',
        'preserve_recent_messages': 'preserve_recent',
        'should_truncate_results': 'truncate_results',  # Also handle the negation
    }
    
    for cli_name, config_name in field_name_mappings.items():
        if cli_name in normalized:
            normalized[config_name] = normalized[cli_name]
            # Keep both for compatibility
    
    # Handle should_truncate_results -> no_truncate_results inversion
    if 'should_truncate_results' in normalized:
        # Invert: should_truncate=True -> no_truncate=False
        normalized['no_truncate_results'] = not normalized['should_truncate_results']
    
    return normalized

def _process_file_loadable_value(value, field_name):
    """
    Process file-loadable values (strings starting with '@').
    
    Args:
        value: The value to process
        field_name: Name of the field (for error messages)
        
    Returns:
        Processed value (file content if @file syntax, otherwise unchanged)
    """
    if not isinstance(value, str):
        return value
    
    if not value.startswith('@'):
        return value
    
    # Extract file path (everything after '@')
    file_path = value[1:]
    
    if not file_path:
        logger.warning(f"Empty file path for field '{field_name}' (value: '{value}')")
        return value
    
    try:
        path_obj = Path(file_path).expanduser().resolve()
        
        if not path_obj.exists():
            logger.warning(f"File not found for field '{field_name}': {file_path}")
            return value
        
        if not path_obj.is_file():
            logger.warning(f"Path is not a file for field '{field_name}': {file_path}")
            return value
        
        with open(path_obj, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.debug(f"Loaded {len(content)} characters from {file_path} for field '{field_name}'")
            return content
            
    except Exception as e:
        logger.warning(f"Failed to load file for field '{field_name}' from {file_path}: {e}")
        return value

def _filter_cli_overrides(cli_args_dict):
    """
    Filter CLI arguments to only include those explicitly set by the user.
    Also processes file-loadable fields (@ syntax).
    
    Excludes:
    - None values (not provided)
    - False values for boolean flags (argparse defaults)
    - Empty lists (not provided)
    - Empty dicts (not provided)
    - Internal/meta arguments (list_profiles, show_config, init_config, profile, config_file)
    
    Processes:
    - File-loadable fields: system_prompt, initial_message, custom_summarization_prompt,
      cli_prompt, response_prefix
    """
    # Arguments that are meta/control and shouldn't be in config
    meta_args = {'list_profiles', 'show_config', 'init_config', 'profile', 'config_file'}
    
    # Fields that support @file syntax
    file_loadable_fields = {
        'system_prompt', 'initial_message', 'custom_summarization_prompt',
        'cli_prompt', 'response_prefix'
    }
    
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
        
        # Skip empty dicts (dataclass-args defaults)
        if isinstance(value, dict) and len(value) == 0:
            continue
        
        # Process file-loadable fields
        if key in file_loadable_fields:
            value = _process_file_loadable_value(value, key)
        
        # Include the (possibly processed) value
        filtered[key] = value
    
    # Normalize field names for profile-config compatibility
    return _normalize_cli_field_names(filtered)


def parse_config() -> YacbaConfig:
    """
    Main configuration parsing entry point.
    
    Uses profile-config 1.1's flexible overrides to coordinate all configuration sources:
    1. Default values (lowest precedence)
    2. Environment variables
    3. Configuration files (with profiles via profile-config discovery)
    4. --config-file (user-specified override file)
    5. CLI arguments (highest precedence)
    
    dataclass-args handles dict fields (model_config, summarization_model_config) with
    automatic file loading and property overrides.
    
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
                        'show_tool_use': True,
                        'model_config': {
                            'temperature': 0.7,
                            'max_tokens': 2000
                        }
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
            print("\nModel configuration can be specified inline or via file:")
            print("  - Inline: model_config: { temperature: 0.7, max_tokens: 2000 }")
            print("  - CLI override: --model-config params.json --mc temperature:0.8")
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
        
        # Add user-specified config file
        if getattr(cli_args, 'config_file', None):
            overrides_list.append(cli_args.config_file)
            logger.info(f"Added config file override: {cli_args.config_file}")
        
        # Add CLI arguments (highest precedence) - only those explicitly set
        cli_overrides = _filter_cli_overrides(vars(cli_args))
        if cli_overrides:
            overrides_list.append(cli_overrides)
            logger.debug(f"Added {len(cli_overrides)} CLI arguments to overrides: {list(cli_overrides.keys())}")

        # 3. Use profile-config with flexible overrides
        try:
            resolver = ProfileConfigResolver(
                config_name=PROFILE_CONFIG_NAME,
                profile_filename=PROFILE_CONFIG_PROFILE_FILE_NAME,
                profile=cli_args.profile or "default",
                extensions=["yaml", "yml"],
                search_home=True,
                overrides=overrides_list
            )
            yacba_config = resolver.resolve()
            logger.info(f"Configuration resolved for profile '{cli_args.profile or 'default'}' with {len(overrides_list)} override sources")
        except ConfigNotFoundError:
            # No discovered files, but overrides still apply
            logger.debug("No configuration file found, using overrides only")
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
            if cli_overrides.get('system_prompt'):
                prompt_source = "command line"
            elif ARGUMENTS_FROM_ENV_VARS.get('system_prompt'):
                prompt_source = "environment"
            else:
                prompt_source = "configuration file"

        # 7. Create YacbaConfig from resolved configuration
        # Use 'model' from profile-config (normalized from 'model_string' in CLI)
        config = YacbaConfig(
            # Core required fields
            model_string=yacba_config.get('model'),
            system_prompt=yacba_config.get('system_prompt'),
            prompt_source=prompt_source,
            tool_config_paths=tool_configs,
            startup_files_content=None,  # Set later in lifecycle

            # Model configuration (dataclass-args handled file loading and property overrides)
            model_config=yacba_config.get('model_config', {}),
            summarization_model_config=yacba_config.get('summarization_model_config', {}),
            emulate_system_prompt=yacba_config.get('emulate_system_prompt', False),

            # File handling
            files_to_upload=files_to_upload,
            max_files=yacba_config.get('max_files', 20),

            # Session management - use 'session' from profile-config (normalized from 'session_name')
            session_name=yacba_config.get('session'),
            agent_id=yacba_config.get('agent_id'),

            # Conversation management - use short names from profile-config
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

        logger.debug("Configuration parsing completed using dataclass-args + profile-config")
        return config

    except Exception as e:
        logger.error(f"Configuration parsing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
