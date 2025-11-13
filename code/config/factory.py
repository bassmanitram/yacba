"""
Configuration factory for YACBA using dataclass-args with base_configs.

This module orchestrates configuration from multiple sources using dataclass-args'
base_configs feature, which handles precedence automatically:

Precedence (lowest to highest):
1. ARGUMENT_DEFAULTS (fallback values)
2. Profile file values (from profile-config)
3. Environment variables (YACBA_*)
4. --config CLI argument (user-specified config file)
5. CLI arguments (highest precedence)

The orchestration is minimal - profile-config resolves profiles + env vars,
then dataclass-args handles everything else via base_configs parameter.
"""

import os
import sys
import yaml
import argparse
from pathlib import Path

from loguru import logger
from dataclass_args import build_config
from dataclass_args.file_loading import load_file_content
from profile_config import ProfileConfigResolver
from profile_config.exceptions import ConfigNotFoundError, ProfileNotFoundError

from yacba_types import ExitCode
from utils.config_utils import discover_tool_configs

from .arguments import ARGUMENT_DEFAULTS, ARGUMENTS_FROM_ENV_VARS
from .dataclass import YacbaConfig

PROFILE_CONFIG_NAME = ".yacba"
PROFILE_CONFIG_PROFILE_FILE_NAME = "config"


def _process_file_loadable_fields(config_dict: dict) -> dict:
    """
    Process @file syntax in file-loadable fields from profile/env configs.
    
    dataclass-args' cli_file_loadable() only processes @file from CLI args,
    not from base_configs. We need to manually process @file syntax for
    values coming from profiles or environment variables.
    
    Args:
        config_dict: Configuration dictionary
        
    Returns:
        Configuration dictionary with @file values loaded
    """
    file_loadable_fields = [
        'system_prompt', 
        'initial_message', 
        'custom_summarization_prompt',
        'cli_prompt', 
        'response_prefix'
    ]
    
    for field in file_loadable_fields:
        if field in config_dict:
            value = config_dict[field]
            if isinstance(value, str) and value.startswith('@'):
                try:
                    # Strip @ prefix before loading
                    file_path = value[1:]
                    # Use dataclass-args' file loading function
                    loaded_content = load_file_content(file_path)
                    config_dict[field] = loaded_content
                    logger.debug(f"Loaded @file for {field}: {len(loaded_content)} characters")
                except Exception as e:
                    logger.warning(f"Failed to load @file for {field} from {value}: {e}")
    
    return config_dict


def parse_config() -> YacbaConfig:
    """
    Main configuration parsing entry point.
    
    Orchestrates configuration from multiple sources using dataclass-args'
    base_configs feature for automatic precedence handling.
    
    Returns:
        YacbaConfig: Fully validated configuration object
        
    Raises:
        SystemExit: On configuration errors or early-exit commands
    """
    try:
        # Handle --help very early (before any profile resolution)
        if '--help' in sys.argv or '-h' in sys.argv:
            # Use dataclass-args to show help (with defaults only)
            build_config(YacbaConfig, base_configs=ARGUMENT_DEFAULTS)
            sys.exit(0)
        
        # Parse arguments using custom parser that includes meta-arguments
        cli_args, profile_name = _parse_args_with_meta()
        
        # Handle early-exit commands
        if hasattr(cli_args, 'list_profiles') and cli_args.list_profiles:
            _handle_list_profiles()
            sys.exit(0)
            
        if hasattr(cli_args, 'init_config') and cli_args.init_config:
            _handle_init_config(cli_args.init_config)
            sys.exit(0)
        
        # 1. Resolve profile + environment variables
        # This gives us: DEFAULTS < PROFILE < ENVVARS
        profile_config = _resolve_profile_and_env(profile_name)
        
        # 2. Process @file syntax in profile/env values
        # (dataclass-args only processes @file from CLI, not base_configs)
        profile_config = _process_file_loadable_fields(profile_config)
        
        # 3. Use dataclass-args with base_configs
        # This gives us: profile_config < --config < CLI args
        config = build_config(
            YacbaConfig,
            args=_filter_meta_args(sys.argv[1:]),
            base_configs=profile_config
        )
        
        # 4. YACBA-specific post-processing (BEFORE show-config)
        config = _post_process_config(config, profile_config)
        
        # Handle --show-config (after post-processing so we see full config)
        if hasattr(cli_args, 'show_config') and cli_args.show_config:
            _handle_show_config(config)
            sys.exit(0)
        
        logger.debug("Configuration parsing completed")
        return config

    except Exception as e:
        logger.error(f"Configuration parsing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(ExitCode.CONFIG_ERROR)


def _parse_args_with_meta():
    """
    Parse CLI arguments including meta-arguments not in YacbaConfig.
    
    Returns:
        Tuple of (args_namespace, profile_name)
    """
    # Create a minimal parser for meta-arguments only
    meta_parser = argparse.ArgumentParser(add_help=False)
    meta_parser.add_argument('--profile', type=str, default=None)
    meta_parser.add_argument('--list-profiles', action='store_true')
    meta_parser.add_argument('--show-config', action='store_true')
    meta_parser.add_argument('--init-config', type=str, default=None)
    
    # Parse only the meta-arguments (ignore unknown)
    meta_args, _ = meta_parser.parse_known_args()
    
    # Extract profile name (CLI > env > 'default')
    profile_name = meta_args.profile
    if not profile_name:
        profile_name = os.environ.get('YACBA_PROFILE', 'default')
    
    return meta_args, profile_name


def _filter_meta_args(argv):
    """
    Filter out meta-arguments that aren't part of YacbaConfig.
    
    Args:
        argv: Command-line arguments list
        
    Returns:
        Filtered arguments list
    """
    filtered = []
    skip_next = False
    
    for arg in argv:
        if skip_next:
            skip_next = False
            continue
            
        if arg in ['--profile', '--init-config']:
            skip_next = True  # Skip the value too
            continue
        elif arg in ['--list-profiles', '--show-config']:
            continue  # Skip flag
        else:
            filtered.append(arg)
    
    return filtered


def _extract_profile_name() -> str:
    """Extract profile name from CLI arguments or environment."""
    # Check CLI first
    if '--profile' in sys.argv:
        idx = sys.argv.index('--profile')
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    
    # Check environment
    profile = os.environ.get('YACBA_PROFILE', 'default')
    return profile


def _resolve_profile_and_env(profile_name: str) -> dict:
    """
    Resolve configuration from profile file and environment variables.
    
    Returns a dictionary with precedence: DEFAULTS < PROFILE < ENVVARS
    
    Args:
        profile_name: Name of profile to load
        
    Returns:
        Dictionary with merged configuration
    """
    # Build overrides list for profile-config
    overrides_list = []
    
    # Add environment variables
    if ARGUMENTS_FROM_ENV_VARS:
        overrides_list.append(ARGUMENTS_FROM_ENV_VARS)
        logger.debug(f"Added {len(ARGUMENTS_FROM_ENV_VARS)} environment variables")
    
    # Resolve with profile-config
    try:
        resolver = ProfileConfigResolver(
            config_name=PROFILE_CONFIG_NAME,
            profile_filename=PROFILE_CONFIG_PROFILE_FILE_NAME,
            profile=profile_name,
            extensions=["yaml", "yml"],
            search_home=True,
            overrides=overrides_list if overrides_list else None
        )
        profile_config = resolver.resolve()
        logger.info(f"Configuration resolved for profile '{profile_name}'")
    except ConfigNotFoundError:
        # No profile file found, use defaults + env vars
        logger.debug("No configuration file found, using defaults + environment variables")
        profile_config = ARGUMENT_DEFAULTS.copy()
        
        # Apply env vars manually
        if ARGUMENTS_FROM_ENV_VARS:
            for key, value in ARGUMENTS_FROM_ENV_VARS.items():
                if value is not None:
                    profile_config[key] = value
    except ProfileNotFoundError:
        logger.error(f"Profile '{profile_name}' not found in configuration")
        sys.exit(ExitCode.CONFIG_ERROR)
    
    # Apply defaults as fallbacks (only for missing keys)
    for key, default_value in ARGUMENT_DEFAULTS.items():
        if key not in profile_config:
            profile_config[key] = default_value
            logger.debug(f"Applied default for missing key '{key}'")
    
    return profile_config


def _post_process_config(config: YacbaConfig, profile_config: dict) -> YacbaConfig:
    """
    Apply YACBA-specific post-processing to configuration.
    
    Args:
        config: Configuration from dataclass-args
        profile_config: Profile configuration for comparison
        
    Returns:
        Updated configuration with post-processing applied
    """
    # Determine system prompt source
    prompt_source = "default"
    if config.system_prompt != ARGUMENT_DEFAULTS.get('system_prompt'):
        # Check if it came from CLI (would be different from profile)
        if profile_config.get('system_prompt') != config.system_prompt:
            prompt_source = "command line"
        elif ARGUMENTS_FROM_ENV_VARS.get('system_prompt'):
            prompt_source = "environment"
        else:
            prompt_source = "configuration file"
    
    # Tool discovery
    tool_config_paths = []
    tool_discovery_result = None
    
    if config.tool_configs_dir:
        tool_config_paths, tool_discovery_result = discover_tool_configs(
            config.tool_configs_dir
        )
        logger.info(f"Discovered {len(tool_config_paths)} tool configurations")
    
    # Create updated config with post-processed fields
    # Note: dataclass is immutable, so we create a new instance
    config_dict = vars(config).copy()
    config_dict['prompt_source'] = prompt_source
    config_dict['tool_config_paths'] = tool_config_paths
    config_dict['tool_discovery_result'] = tool_discovery_result
    
    return YacbaConfig(**config_dict)


def _handle_list_profiles():
    """Handle --list-profiles command."""
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
        print(f"No configuration file found. Expected at ./{PROFILE_CONFIG_NAME}/config.yaml or ~/{PROFILE_CONFIG_NAME}/config.yaml")


def _handle_init_config(output_path_str: str):
    """Handle --init-config command."""
    output_path = Path(output_path_str).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    sample_config = {
        'default_profile': 'development',
        'defaults': {
            'conversation_manager_type': 'sliding_window',
            'sliding_window_size': 40,
            'max_files': 10
        },
        'profiles': {
            'development': {
                'model_string': 'litellm:gemini/gemini-1.5-flash',
                'system_prompt': 'You are a helpful development assistant with access to tools.',
                'tool_configs_dir': '~/.yacba/tools/',
                'show_tool_use': True,
                'model_config': {
                    'temperature': 0.7,
                    'max_tokens': 2000
                }
            },
            'production': {
                'model_string': 'openai:gpt-4',
                'system_prompt': '@~/.yacba/prompts/production.txt',
                'tool_configs_dir': '~/.yacba/tools/production/',
                'show_tool_use': False,
                'conversation_manager_type': 'summarizing',
                'session_name': 'prod-session'
            },
            'coding': {
                'inherits': 'development',
                'model_string': 'anthropic:claude-3-sonnet',
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
    print(f"  - ./{PROFILE_CONFIG_NAME}/config.yaml (project-specific)")
    print(f"  - ~/{PROFILE_CONFIG_NAME}/config.yaml (user-wide)")


def _handle_show_config(config: YacbaConfig):
    """Handle --show-config command."""
    print("Resolved configuration:")
    config_dict = vars(config)
    for key, value in sorted(config_dict.items()):
        # Skip large/complex internal fields
        if key in ['startup_files_content', 'tool_discovery_result']:
            print(f"  {key}: <internal>")
        elif key == 'system_prompt' and value and len(str(value)) > 100:
            # Truncate long system prompts
            print(f"  {key}: {repr(str(value)[:100])}... ({len(str(value))} chars)")
        else:
            print(f"  {key}: {repr(value)}")
