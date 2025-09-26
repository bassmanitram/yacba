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
import argparse
from typing import Dict, Any, Optional, List
from pathlib import Path
from loguru import logger

from .file_loader import ConfigManager
from .argument_definitions import ARGUMENT_DEFINITIONS
from .dataclass import YacbaConfig
from utils.config_discovery import discover_tool_configs
from utils.file_utils import guess_mimetype, validate_file_path, get_file_size
from utils.model_config_parser import parse_model_config, ModelConfigError
from yacba_types.config import ToolDiscoveryResult, ModelConfig, FileUpload


def _create_integrated_parser() -> argparse.ArgumentParser:
    """
    Create argument parser with configuration file integration.
    
    This is similar to unified_parser but includes config file arguments.
    """
    parser = argparse.ArgumentParser(
        description="YACBA - Yet Another ChatBot Agent",
        add_help=False  # We'll add help manually to control order
    )
    
    # Add configuration file arguments first
    parser.add_argument('--config', help="Path to configuration file")
    parser.add_argument('--profile', help="Configuration profile to use")
    parser.add_argument('--list-profiles', action='store_true', help="List available profiles and exit")
    parser.add_argument('--show-config', action='store_true', help="Show resolved configuration and exit")
    parser.add_argument('--init-config', help="Create sample configuration file at path")
    parser.add_argument('-h', '--help', action='help', help="Show this help message and exit")
    
    # Add all regular arguments from definitions
    for arg_def in ARGUMENT_DEFINITIONS:
        # Skip config-related args already added above
        if any(name in ['--config', '--profile', '--list-profiles', '--show-config', '--init-config'] 
               for name in arg_def.names):
            continue
            
        kwargs = {'help': arg_def.help}
        
        if arg_def.argtype:
            kwargs['type'] = arg_def.argtype
        if arg_def.action:
            kwargs['action'] = arg_def.action
        if arg_def.default_factory:
            kwargs['default'] = arg_def.default_factory()
        elif arg_def.default is not None:
            kwargs['default'] = arg_def.default
        if arg_def.choices:
            kwargs['choices'] = arg_def.choices
        if arg_def.nargs:
            kwargs['nargs'] = arg_def.nargs
        if arg_def.required:
            kwargs['required'] = arg_def.required
        if arg_def.action == "append":
            kwargs['dest'] = arg_def.attr_name
            
        parser.add_argument(*arg_def.names, **kwargs)
    
    return parser


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


def _create_model_config(model_string: str, config_file: Optional[str] = None, 
                        config_overrides: Optional[List[str]] = None) -> ModelConfig:
    """
    Create a ModelConfig object from the model string and additional parameters.
    
    Args:
        model_string: The model string in format 'framework:model'
        config_file: Optional path to model configuration JSON file
        config_overrides: Optional list of configuration overrides
        
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
    
    # Parse model configuration from file and overrides
    try:
        model_config_dict = parse_model_config(config_file, config_overrides)
        logger.debug(f"Parsed model config: {len(model_config_dict)} properties")
    except ModelConfigError as e:
        logger.error(f"Model configuration error: {e}")
        raise ValueError(f"Model configuration error: {e}")
    
    # Add framework and model_id to the config dict
    model_config_dict['framework'] = framework
    model_config_dict['model_id'] = model_id
    
    # Create ModelConfig with all the configuration
    model_config = ModelConfig(**model_config_dict)
    
    return model_config


def _merge_config_with_args(args: argparse.Namespace, config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge configuration file values with CLI arguments.
    CLI arguments take precedence over config file values.
    
    Args:
        args: Parsed CLI arguments
        config_dict: Configuration from file
        
    Returns:
        Merged configuration dictionary
    """
    merged = config_dict.copy()
    
    # Simple approach: Override any field that exists in args and has a non-default value
    # This is more reliable than trying to match argument definitions
    
    # Create a mapping of known CLI fields to their config file equivalents
    cli_to_config_mapping = {
        'model': 'model',
        'system_prompt': 'system_prompt', 
        'headless': 'headless',
        'initial_message': 'initial_message',
        'max_files': 'max_files',
        'session': 'session',
        'agent_id': 'agent_id',
        'conversation_manager': 'conversation_manager',
        'window_size': 'window_size',
        'preserve_recent': 'preserve_recent',
        'summary_ratio': 'summary_ratio',
        'summarization_model': 'summarization_model',
        'custom_summarization_prompt': 'custom_summarization_prompt',
        'no_truncate_results': 'no_truncate_results',
        'show_tool_use': 'show_tool_use',
        'emulate_system_prompt': 'emulate_system_prompt',
        'clear_cache': 'clear_cache',
        'files': 'files',
        'tool_configs_dir': 'tool_configs_dir',
        'model_config': 'model_config',
        'c': 'config_overrides'  # This is the append field
    }
    
    # Get defaults to compare against
    import os
    defaults = {
        'model': os.environ.get("YACBA_MODEL_ID", "litellm:gemini/gemini-2.5-flash"),
        'system_prompt': os.environ.get("YACBA_SYSTEM_PROMPT", 
            "You are a general assistant with access to various tools to enhance your capabilities. "
            "You are NOT a specialized assistant dedicated to any specific tool provider."),
        'session': os.environ.get("YACBA_SESSION_NAME", "default"),
        'headless': False,
        'initial_message': None,
        'max_files': 10,
        'conversation_manager': 'sliding_window',
        'window_size': 40,
        'preserve_recent': 10,
        'summary_ratio': 0.3,
        'show_tool_use': False,
        'emulate_system_prompt': False,
        'clear_cache': False,
        'files': [],
        'tool_configs_dir': None,  # Changed from [] to None since it's now a single string
    }
    
    # Override config file values with CLI values that differ from defaults
    for cli_field, config_field in cli_to_config_mapping.items():
        if hasattr(args, cli_field):
            cli_value = getattr(args, cli_field)
            default_value = defaults.get(cli_field)
            
            # Override if CLI value is different from default or if it's a list/None field
            if (cli_value != default_value or 
                cli_value is not None or 
                isinstance(cli_value, list)):
                merged[config_field] = cli_value
                logger.debug(f"CLI override: {config_field} = {cli_value}")
    
    # Add CLI-only values that aren't in config file mapping
    cli_only_fields = ['config', 'profile', 'list_profiles', 'show_config', 'init_config']
    for field in cli_only_fields:
        if hasattr(args, field):
            merged[field] = getattr(args, field)
    
    return merged


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
        parser = _create_integrated_parser()
        args = parser.parse_args()
        
        logger.debug(f"Parsed CLI arguments: {args}")
        
        # Handle special commands that exit immediately
        if args.list_profiles:
            config_manager = ConfigManager()
            profiles = config_manager.list_profiles()
            if profiles:
                print("Available profiles:")
                for profile in profiles:
                    print(f"  - {profile}")
            else:
                print("No profiles found in configuration file.")
            sys.exit(0)
        
        if args.init_config:
            config_manager = ConfigManager()
            config_manager.create_sample_config(args.init_config)
            print(f"Configuration file created at: {args.init_config}")
            sys.exit(0)
        
        # Load configuration file if specified or discoverable
        config_dict = {}
        if args.config or args.profile:
            config_manager = ConfigManager()
            config_dict = config_manager.load_config(
                config_path=args.config,
                profile=args.profile  # Fixed: was profile_name
            )
            logger.info(f"Loaded configuration from file with profile: {args.profile or 'default'}")
        
        if args.show_config:
            # Show merged configuration and exit
            merged = _merge_config_with_args(args, config_dict)
            import yaml
            print("Resolved configuration:")
            print(yaml.dump(merged, default_flow_style=False))
            sys.exit(0)
        
        # Merge config file with CLI arguments
        merged_config = _merge_config_with_args(args, config_dict)
        
        logger.debug(f"Merged configuration: {merged_config}")
        
        # Process complex fields that need special handling
        
        # 1. Process file uploads
        files_to_upload = []
        files_list = merged_config.get('files')
        if files_list and isinstance(files_list, list) and len(files_list) > 0:
            files_to_upload = _process_file_uploads(files_list)
            logger.info(f"Processed {len(files_to_upload)} file uploads")
        
        # 2. Discover and process tool configurations  
        tool_configs = []
        tool_discovery_result = ToolDiscoveryResult([], [], 0)
        tool_configs_dir = merged_config.get('tool_configs_dir')
        # Now handle single directory path (string) instead of list
        if tool_configs_dir and isinstance(tool_configs_dir, str) and tool_configs_dir.strip():
            tool_configs, tool_discovery_result = discover_tool_configs(tool_configs_dir)
            logger.info(f"Discovered {len(tool_configs)} tool configurations from directory: {tool_configs_dir}")
        
        # 3. Create model configuration
        model_config = _create_model_config(
            merged_config.get('model'),
            merged_config.get('model_config'),
            merged_config.get('config_overrides')
        )
        
        # 4. Determine prompt source
        import os
        default_system_prompt = os.environ.get("YACBA_SYSTEM_PROMPT", 
            "You are a general assistant with access to various tools to enhance your capabilities. "
            "You are NOT a specialized assistant dedicated to any specific tool provider.")
        
        prompt_source = "default"
        if os.environ.get("YACBA_SYSTEM_PROMPT"):
            prompt_source = "environment"
        if merged_config.get('system_prompt') != default_system_prompt:
            if 'system_prompt' in config_dict:
                prompt_source = "config-file"
            else:
                prompt_source = "command-line"
        
        # 5. Validate configuration before creating YacbaConfig
        if merged_config.get('headless') and not merged_config.get('initial_message'):
            raise ValueError("Headless mode requires an initial message via --initial-message")
        
        # Create YacbaConfig directly from merged configuration
        config = YacbaConfig(
            # Core required fields
            model_string=merged_config.get('model'),
            system_prompt=merged_config.get('system_prompt', default_system_prompt),
            prompt_source=prompt_source,
            tool_configs=tool_configs,
            startup_files_content=None,  # Set later in lifecycle
            
            # Model configuration
            model_config=model_config,
            emulate_system_prompt=merged_config.get('emulate_system_prompt', False),
            
            # File handling
            files_to_upload=files_to_upload,
            max_files=merged_config.get('max_files', 20),
            
            # Session management
            session_name=merged_config.get('session'),
            agent_id=merged_config.get('agent_id'),
            
            # Conversation management
            conversation_manager_type=merged_config.get('conversation_manager', 'sliding_window'),
            sliding_window_size=merged_config.get('window_size', 40),
            preserve_recent_messages=merged_config.get('preserve_recent', 10),
            summary_ratio=merged_config.get('summary_ratio', 0.3),
            summarization_model=merged_config.get('summarization_model'),
            custom_summarization_prompt=merged_config.get('custom_summarization_prompt'),
            should_truncate_results=not merged_config.get('no_truncate_results', False),
            
            # Execution mode
            headless=merged_config.get('headless', False),
            initial_message=merged_config.get('initial_message'),
            
            # Output control
            show_tool_use=merged_config.get('show_tool_use', False),
            
            # Performance
            clear_cache=merged_config.get('clear_cache', False),
            show_perf_stats=merged_config.get('show_perf_stats', False),
            disable_cache=merged_config.get('disable_cache', False),
            
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