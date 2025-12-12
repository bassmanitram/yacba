"""
Configuration factory for YACBA using dataclass-args with cli_nested.

This module orchestrates configuration from multiple sources using dataclass-args'
cli_nested feature to compose AgentFactoryConfig directly with YACBA-specific config.

Precedence (lowest to highest):
1. Defaults (ARGUMENT_DEFAULTS - YACBA overrides of strands-agent-factory defaults)
2. Profile file values (from profile-config)
3. Environment variables (YACBA_*)
4. --config CLI argument (user-specified config file)
5. CLI arguments (highest precedence)

With cli_nested, there is NO converter - config.agent IS AgentFactoryConfig!
"""

import os
import sys
import yaml
import argparse
import mimetypes
import re
from pathlib import Path
from typing import List, Tuple, Dict, Any

from utils.logging import get_logger
from utils.session_utils import get_sessions_home
from dataclass_args import build_config
from dataclass_args.file_loading import load_file_content
from profile_config import ProfileConfigResolver
from profile_config.exceptions import ConfigNotFoundError, ProfileNotFoundError
from repl_toolkit import print_formatted_text, auto_format

from yacba_types import ExitCode, FileUpload
from utils.config_utils import discover_tool_configs
from utils.file_utils import validate_file_path, get_file_size, resolve_glob

from .arguments import ARGUMENT_DEFAULTS, ARGUMENTS_FROM_ENV_VARS
from .dataclass import YacbaConfig

logger = get_logger(__name__)

PROFILE_CONFIG_NAME = ".yacba"
PROFILE_CONFIG_PROFILE_FILE_NAME = "config"

# Regex for validating MIME type format (type/subtype)
_MT_CHARS = r"[a-zA-Z0-9][a-zA-Z0-9!#$&^_.+-]*"
_BASIC_MT = re.compile(fr"^{_MT_CHARS}/{_MT_CHARS}$", re.IGNORECASE)


def _validate_and_expand_files(files_args: List[List[str]]) -> List[Tuple[str, str]]:
    """
    Validate and expand file arguments from -f flags.
    
    Each entry in files_args is [FILE_GLOB] or [FILE_GLOB, MIMETYPE].
    - Validates mimetype format if provided
    - Expands glob patterns using resolve_glob() (supports bracket syntax)
    - Guesses mimetype if not provided
    
    Args:
        files_args: List of argument lists from cli_append
        
    Returns:
        List of (path, mimetype) tuples
    """
    result = []
    
    for file_spec in files_args:
        file_glob = file_spec[0]
        mimetype = file_spec[1] if len(file_spec) == 2 else None
        
        # Validate mimetype format if provided
        if mimetype:
            if not _BASIC_MT.fullmatch(mimetype):
                logger.warning(
                    "invalid_mimetype_format",
                    mimetype=mimetype,
                    pattern=file_glob,
                    message=f"Mimetype '{mimetype}' must be in format 'type/subtype'. Skipping this file spec."
                )
                continue
        
        # Expand glob pattern
        try:
            globbed_files = resolve_glob(file_glob)
            if not globbed_files:
                # No matches - add the pattern as-is (will error later if file doesn't exist)
                globbed_files = [file_glob]
        except Exception as e:
            logger.warning(
                "glob_expansion_failed",
                pattern=file_glob,
                error=str(e),
                message=f"Failed to expand glob pattern '{file_glob}': {e}. Skipping."
            )
            continue
        
        # Add each file with mimetype
        for file_path in globbed_files:
            if mimetype:
                result.append((file_path, mimetype))
            else:
                # Guess mimetype
                guessed, _ = mimetypes.guess_type(file_path)
                result.append((file_path, guessed or "text/plain"))
    
    return result


def _process_file_uploads(file_tuples: List[Tuple[str, str]]) -> List[FileUpload]:
    """
    Process file (path, mimetype) tuples and create FileUpload objects.

    Args:
        file_tuples: List of (path, mimetype) tuples

    Returns:
        List of FileUpload objects

    Raises:
        FileNotFoundError: If a file doesn't exist
        ValueError: If a file is not readable
    """
    uploads = []

    for path_str, mimetype in file_tuples:
        try:
            # Validate the path
            path = Path(path_str).expanduser().resolve()
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


def _process_file_loadable_fields(config_dict: dict) -> dict:
    """
    Process @file syntax in file-loadable fields from profile/env configs.

    dataclass-args' cli_file_loadable() only processes @file from CLI args,
    not from base_configs. We need to manually process @file syntax for
    values coming from profiles or environment variables.

    Args:
        config_dict: Configuration dictionary (nested structure)

    Returns:
        Configuration dictionary with @file values loaded
    """
    def process_dict(d: dict):
        """Recursively process dictionary"""
        for key, value in d.items():
            if isinstance(value, dict):
                process_dict(value)
            elif isinstance(value, str) and value.startswith("@"):
                try:
                    # Strip @ prefix before loading
                    file_path = value[1:]
                    # Use dataclass-args' file loading function
                    loaded_content = load_file_content(file_path)
                    d[key] = loaded_content
                    logger.debug("file_loaded", field=key, length=len(loaded_content))
                except Exception as e:
                    logger.warning(
                        "file_load_failed", field=key, path=value, error=str(e)
                    )
    
    process_dict(config_dict)
    return config_dict


def _load_config_file(file_path: str) -> dict:
    """
    Load a config file.
    
    Expects nested structure with 'agent' and/or 'repl' sections.
    
    Args:
        file_path: Path to config file
        
    Returns:
        Configuration dict (nested structure)
        
    Raises:
        ValueError: If config file is not in nested format
    """
    with open(file_path, 'r') as f:
        config_dict = yaml.safe_load(f)
    
    # Validate nested structure
    if not isinstance(config_dict, dict):
        raise ValueError(f"Config file must be a YAML dictionary: {file_path}")
    
    if "agent" not in config_dict and "repl" not in config_dict:
        raise ValueError(
            f"Config file must use nested structure with 'agent' and/or 'repl' sections. "
            f"See MIGRATION_NESTED_CONFIG.md for migration guide. File: {file_path}"
        )
    
    # Process @file syntax
    config_dict = _process_file_loadable_fields(config_dict)
    
    return config_dict


def parse_config() -> YacbaConfig:
    """
    Main configuration parsing entry point.

    Orchestrates configuration from multiple sources using dataclass-args'
    cli_nested feature for direct composition.

    Returns:
        YacbaConfig: Fully validated configuration object

    Raises:
        SystemExit: On configuration errors or early-exit commands
    """
    try:
        # Handle --help very early (before any profile resolution)
        if "--help" in sys.argv or "-h" in sys.argv:
            # Temporarily override sys.argv[0] for help display
            original_argv0 = sys.argv[0]
            sys.argv[0] = "yacba"

            try:
                # Use dataclass-args to show help (with defaults from nested configs)
                build_config(YacbaConfig)
            except SystemExit:
                # Catch the exit from build_config to add our subcommand help
                sys.argv[0] = original_argv0

                print("\nSubcommands (use without dash prefix):")
                print("  version           Show version information")
                print("  doctor            Run health check and show installation status")
                print("  list-extras       Show available model providers and tools")
                print("  install-extras    Install additional providers or tools")
                print("  link              Create symlink to launcher")
                print("  self-update       Update YACBA to latest version")
                print("  upgrade-deps      Upgrade dependencies to latest versions")
                print("  uninstall         Remove YACBA installation")
                print("\nExamples:")
                print("  yacba version")
                print("  yacba doctor")
                print("  yacba list-extras")
                print("  yacba install-extras anthropic openai")

                sys.exit(0)

        # Parse arguments using custom parser that includes meta-arguments
        cli_args, profile_name = _parse_args_with_meta()

        # Handle early-exit commands
        if hasattr(cli_args, "list_profiles") and cli_args.list_profiles:
            _handle_list_profiles()
            sys.exit(0)

        if hasattr(cli_args, "init_config") and cli_args.init_config:
            _handle_init_config(cli_args.init_config)
            sys.exit(0)

        # 1. Resolve profile + environment variables
        profile_config = _resolve_profile_and_env(profile_name)
        
        # 2. Process @file syntax in profile/env values
        profile_config = _process_file_loadable_fields(profile_config)

        # 3. Use dataclass-args with base_configs
        # Temporarily override sys.argv[0] for better help output
        original_argv0 = sys.argv[0]
        sys.argv[0] = "yacba"

        try:
            # Check if --config is specified and process it
            config_file_path = None
            if "--config" in sys.argv:
                idx = sys.argv.index("--config")
                if idx + 1 < len(sys.argv):
                    config_file_path = sys.argv[idx + 1]
            
            # Filter args (including --config since we handle it manually)
            filtered_args = _filter_meta_args(sys.argv[1:], also_filter_config=True)
            
            # Load --config file if specified
            config_file_configs = []
            if config_file_path:
                try:
                    loaded_config = _load_config_file(config_file_path)
                    config_file_configs.append(loaded_config)
                except ValueError as e:
                    logger.error(f"Configuration file error: {e}")
                    sys.exit(ExitCode.CONFIG_ERROR)
            
            # Build base_configs list: profile_config < config_file_configs
            all_base_configs = [profile_config]
            if config_file_configs:
                all_base_configs.extend(config_file_configs)
            
            config = build_config(
                YacbaConfig,
                args=filtered_args,
                base_configs=all_base_configs,
            )
        finally:
            sys.argv[0] = original_argv0

        # 4. YACBA-specific post-processing
        config = _post_process_config(config)

        # Handle --show-config (after post-processing so we see full config)
        if hasattr(cli_args, "show_config") and cli_args.show_config:
            _handle_show_config(config)
            sys.exit(0)

        logger.debug("configuration_parsing_completed")
        return config

    except Exception as e:
        logger.error("Configuration parsing failed: %s", str(e), exc_info=True)
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
    meta_parser.add_argument("--profile", type=str, default=None)
    meta_parser.add_argument("--list-profiles", action="store_true")
    meta_parser.add_argument("--show-config", action="store_true")
    meta_parser.add_argument("--init-config", type=str, default=None)

    # Parse only the meta-arguments (ignore unknown)
    meta_args, _ = meta_parser.parse_known_args()

    # Extract profile name (CLI > env > 'default')
    profile_name = meta_args.profile
    if not profile_name:
        profile_name = os.environ.get("YACBA_PROFILE", "default")

    return meta_args, profile_name


def _filter_meta_args(argv, also_filter_config=False):
    """
    Filter out meta-arguments that aren't part of YacbaConfig.

    Args:
        argv: Command-line arguments list
        also_filter_config: If True, also filter --config (for manual handling)

    Returns:
        Filtered arguments list
    """
    filtered = []
    skip_next = False

    for arg in argv:
        if skip_next:
            skip_next = False
            continue

        if arg in ["--profile", "--init-config"]:
            skip_next = True  # Skip the value too
            continue
        elif arg == "--config" and also_filter_config:
            skip_next = True  # Skip the value too when manually handling
            continue
        elif arg in ["--list-profiles", "--show-config"]:
            continue  # Skip flag
        else:
            filtered.append(arg)

    return filtered


def _resolve_profile_and_env(profile_name: str) -> dict:
    """
    Resolve configuration from profile file and environment variables.

    Returns a dictionary with precedence: ARGUMENT_DEFAULTS < PROFILE < ENVVARS

    This function ALWAYS starts with ARGUMENT_DEFAULTS as the base layer to ensure
    YACBA's default overrides (like agent_id) are preserved even when a profile
    config file exists but doesn't specify those fields.

    Args:
        profile_name: Name of profile to load

    Returns:
        Dictionary with nested configuration structure
        
    Raises:
        SystemExit: If profile not found or config structure invalid
    """
    # Start with ARGUMENT_DEFAULTS as the base layer
    # Use deep copy to avoid modifying the original
    profile_config = {}
    for key, value in ARGUMENT_DEFAULTS.items():
        if isinstance(value, dict):
            profile_config[key] = value.copy()  # Shallow copy nested dicts
        else:
            profile_config[key] = value
    
    logger.debug("starting_with_argument_defaults", defaults_keys=list(ARGUMENT_DEFAULTS.keys()))

    # Build overrides list for profile-config
    overrides_list = []

    # Add environment variables (already in nested structure from arguments.py)
    if ARGUMENTS_FROM_ENV_VARS:
        overrides_list.append(ARGUMENTS_FROM_ENV_VARS)
        logger.debug("environment_variables_added", count=len(ARGUMENTS_FROM_ENV_VARS))

    # Resolve with profile-config
    try:
        resolver = ProfileConfigResolver(
            config_name=PROFILE_CONFIG_NAME,
            profile_filename=PROFILE_CONFIG_PROFILE_FILE_NAME,
            profile=profile_name,
            extensions=["yaml", "yml"],
            search_home=True,
            overrides=overrides_list if overrides_list else None,
        )
        resolved_profile = resolver.resolve()
        
        # Validate nested structure
        if resolved_profile and not isinstance(resolved_profile, dict):
            logger.error("profile_config_invalid", profile=profile_name, type=type(resolved_profile))
            sys.exit(ExitCode.CONFIG_ERROR)
        
        if resolved_profile and "agent" not in resolved_profile and "repl" not in resolved_profile:
            logger.error(
                "profile_config_not_nested",
                profile=profile_name,
                message="Profile config must use nested structure. See MIGRATION_NESTED_CONFIG.md"
            )
            sys.exit(ExitCode.CONFIG_ERROR)
        
        # Deep merge resolved profile into base (which already has ARGUMENT_DEFAULTS)
        if resolved_profile:
            _deep_merge(profile_config, resolved_profile)
            logger.info("profile_resolved_and_merged", profile=profile_name)
        
    except ConfigNotFoundError:
        # No profile file found - that's fine, we already have ARGUMENT_DEFAULTS in profile_config
        logger.debug("no_config_file_found_using_defaults")
        
        # Still apply env vars manually since they weren't processed by profile-config
        if overrides_list:
            for override in overrides_list:
                _deep_merge(profile_config, override)
                
    except ProfileNotFoundError:
        logger.error("profile_not_found", profile=profile_name)
        sys.exit(ExitCode.CONFIG_ERROR)

    return profile_config


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override dict into base dict."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def _post_process_config(config: YacbaConfig) -> YacbaConfig:
    """
    Apply YACBA-specific post-processing to configuration.
    
    This handles:
    - Setting output_printer (can't be in CLI)
    - Setting sessions_home (computed from session_id)
    - Pre-formatting response_prefix (XML parsing fix)
    - Processing file uploads
    - Determining prompt source

    Args:
        config: Configuration from dataclass-args

    Returns:
        Updated configuration with post-processing applied
    """
    # Determine system prompt source
    prompt_source = "default"
    if config.agent.system_prompt:
        # Check if it's not the default
        from strands_agent_factory import AgentFactoryConfig
        default_prompt = AgentFactoryConfig().system_prompt
        if config.agent.system_prompt != default_prompt:
            prompt_source = "configuration"  # Could be CLI, config file, or env
    
    # Set output_printer (can't be specified via CLI)
    config.agent.output_printer = (
        print_formatted_text if not config.repl.headless else print
    )
    
    # Pre-format response_prefix to prevent XML parsing issues
    if config.agent.response_prefix:
        config.agent.response_prefix = auto_format(config.agent.response_prefix)
    
    # Compute sessions_home if session_id is set
    if config.agent.session_id and not config.agent.sessions_home:
        config.agent.sessions_home = get_sessions_home()
        logger.debug("sessions_home_computed", path=config.agent.sessions_home)
    
    # Process file uploads from config.agent.file_paths
    # file_paths comes from -f CLI argument (via AgentFactoryConfig)
    files_to_upload = []
    if config.agent.file_paths:
        # file_paths is already List[List[str]] from cli_append
        files_list = _validate_and_expand_files(config.agent.file_paths)
        logger.debug("files_expanded", count=len(files_list))
        
        # Create FileUpload objects
        files_to_upload = _process_file_uploads(files_list)
        logger.info("files_processed", count=len(files_to_upload))
        
        # Enforce max_files limit
        if len(files_to_upload) > config.repl.max_files:
            logger.warning(
                "file_limit_exceeded",
                provided=len(files_to_upload),
                max=config.repl.max_files
            )
            files_to_upload = files_to_upload[:config.repl.max_files]
    
    # Update internal fields
    config.prompt_source = prompt_source
    config.files_to_upload = files_to_upload
    
    return config


def _handle_list_profiles():
    """Handle --list-profiles command."""
    try:
        resolver = ProfileConfigResolver(
            config_name=PROFILE_CONFIG_NAME,
            profile_filename=PROFILE_CONFIG_PROFILE_FILE_NAME,
            extensions=["yaml", "yml"],
        )
        profiles = resolver.list_profiles()
        if profiles:
            print("Available profiles:")
            for profile in profiles:
                print(f"  - {profile}")
        else:
            print("No profiles found in configuration file.")
    except ConfigNotFoundError:
        print(
            f"No configuration file found. Expected at ./{PROFILE_CONFIG_NAME}/config.yaml or ~/{PROFILE_CONFIG_NAME}/config.yaml"
        )


def _handle_init_config(output_path_str: str):
    """Handle --init-config command."""
    output_path = Path(output_path_str).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Use nested structure in sample config
    sample_config = {
        "default_profile": "development",
        "defaults": {
            "agent": {
                "conversation_manager_type": "sliding_window",
                "sliding_window_size": 40,
            },
            "repl": {
                "max_files": 10,
            },
        },
        "profiles": {
            "development": {
                "agent": {
                    "model": "litellm:gemini/gemini-1.5-flash",
                    "system_prompt": "You are a helpful development assistant with access to tools.",
                    "tool_config_paths": ["~/.yacba/tools/*.json"],
                    "show_tool_use": True,
                    "model_config": {"temperature": 0.7, "max_tokens": 2000},
                },
                "repl": {
                    "headless": False,
                },
            },
            "production": {
                "agent": {
                    "model": "openai:gpt-4",
                    "system_prompt": "@~/.yacba/prompts/production.txt",
                    "tool_config_paths": ["~/.yacba/tools/production/*.json"],
                    "show_tool_use": False,
                    "conversation_manager_type": "summarizing",
                    "session_id": "prod-session",
                },
                "repl": {
                    "headless": False,
                },
            },
            "coding": {
                "inherits": "development",
                "agent": {
                    "model": "anthropic:claude-3-sonnet",
                    "system_prompt": "You are an expert programmer with access to development tools.",
                    "tool_config_paths": ["~/.yacba/tools/dev/*.json"],
                },
                "repl": {
                    "max_files": 50,
                },
            },
        },
    }

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2)

    print(f"Sample configuration created at: {output_path}")
    print("Recommended locations:")
    print(f"  - ./{PROFILE_CONFIG_NAME}/config.yaml (project-specific)")
    print(f"  - ~/{PROFILE_CONFIG_NAME}/config.yaml (user-wide)")


def _handle_show_config(config: YacbaConfig):
    """Handle --show-config command."""
    print("Resolved configuration:")
    print("\n[agent] (AgentFactoryConfig):")
    agent_dict = vars(config.agent)
    for key, value in sorted(agent_dict.items()):
        if key in ["output_printer", "callback_handler"]:
            print(f"  {key}: <function>")
        elif key == "system_prompt" and value and len(str(value)) > 100:
            print(f"  {key}: {repr(str(value)[:100])}... ({len(str(value))} chars)")
        else:
            print(f"  {key}: {repr(value)}")
    
    print("\n[repl] (YacbaREPLConfig):")
    repl_dict = vars(config.repl)
    for key, value in sorted(repl_dict.items()):
        print(f"  {key}: {repr(value)}")
    
    print("\n[internal] (YACBA fields):")
    for key in ["prompt_source", "files_to_upload", "tool_discovery_result"]:
        value = getattr(config, key)
        if key == "files_to_upload" and value:
            print(f"  {key}: {len(value)} files")
        elif key == "tool_discovery_result":
            print(f"  {key}: <internal>")
        else:
            print(f"  {key}: {repr(value)}")
