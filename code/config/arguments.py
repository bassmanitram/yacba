"""
Argument definitions for YACBA using dataclass-args.

This module provides CLI argument parsing using dataclass-args for automatic
argument generation from the YacbaConfig dataclass, with manual handling for:
- Complex custom Actions (FilesSpec)
- Meta-commands (list-profiles, show-config, init-config)
- Arguments requiring short aliases not in dataclass (tool-configs-dir)

Everything else is auto-generated from YacbaConfig with dataclass-args annotations:
- Type inference (str, int, bool, dict, Path, etc.)
- Help text from cli_help()
- Short aliases from cli_short()
- File loading from cli_file_loadable()
- Choices validation from cli_choices()
- Boolean --flag/--no-flag pairs
- Dict file loading and property overrides (--mc, --smc)
"""

import sys
from argparse import Action, ArgumentParser, Namespace
from pathlib import Path
from typing import Dict, Any

from dataclass_args import GenericConfigBuilder

from .dataclass import YacbaConfig

# ============================================================================
# Argument Defaults
# ============================================================================

ARGUMENT_DEFAULTS = {
    'model': 'litellm:gemini/gemini-2.5-flash',
    'system_prompt': (
        "You are a highly capable AI assistant with access to various tools "
        "and the ability to read and analyze files. Provide helpful, accurate, "
        "and contextual responses."
    ),
    'conversation_manager': 'sliding_window',
    'window_size': 40,
    'preserve_recent': 10,
    'summary_ratio': 0.3,
    'max_files': 20,
    'emulate_system_prompt': False,
    'show_tool_use': False,
    'headless': False,
    'no_truncate_results': False,
}

# ============================================================================
# Environment Variables
# ============================================================================

ARGUMENTS_FROM_ENV_VARS: Dict[str, Any] = {}


# ============================================================================
# Custom Actions
# ============================================================================

class FilesSpec(Action):
    """
    Custom argparse Action for handling file specifications with optional mimetypes.
    
    This action supports complex file upload specifications beyond what dataclass-args
    provides automatically.
    
    Format: FILE_GLOB [MIMETYPE]
    - Can be invoked multiple times
    - Accepts 1-2 arguments per invocation
    - Stores results as list of tuples: [(file_glob, mimetype_or_None), ...]
    
    Examples:
        -f file.txt
        -f "*.py"
        -f "data.bin" "application/octet-stream"
        -f file1.txt -f file2.pdf -f "*.md"
    """
    def __call__(self, parser, namespace, values, option_string=None):
        if not isinstance(values, list):
            values = [values]
        
        # Get existing list or create new one
        items = getattr(namespace, self.dest, None)
        if items is None:
            items = []
        
        # Parse the values (1-2 arguments: file_glob, optional mimetype)
        if len(values) == 1:
            items.append((values[0], None))
        elif len(values) == 2:
            items.append((values[0], values[1]))
        else:
            parser.error(f"{option_string} requires 1-2 arguments: FILE_GLOB [MIMETYPE]")
        
        setattr(namespace, self.dest, items)


# ============================================================================
# Argument Parsing
# ============================================================================

def parse_args(args=None) -> Namespace:
    """
    Parse command-line arguments using dataclass-args for automatic generation.
    
    Manual handling for:
    - FilesSpec custom Action (-f/--files)
    - Meta-commands (--profile, --list-profiles, --show-config, --init-config)
    - tool-configs-dir (needs -t short alias, excluded from dataclass)
    
    Returns:
        Namespace with all parsed arguments
    """
    parser = ArgumentParser(
        description="YACBA - Yet Another ChatBot Agent",
        epilog="Use -H for headless mode, -i for initial message"
    )
    
    # 1. Meta-commands (not in YacbaConfig - profile-config coordination)
    parser.add_argument(
        '--profile',
        type=str,
        help="Configuration profile to use"
    )
    parser.add_argument(
        '--config-file',
        type=str,
        help="Path to configuration file (overrides discovered config)"
    )
    parser.add_argument(
        '--list-profiles',
        action='store_true',
        help="List available configuration profiles and exit"
    )
    parser.add_argument(
        '--show-config',
        action='store_true',
        help="Display resolved configuration and exit"
    )
    parser.add_argument(
        '--init-config',
        type=str,
        metavar='PATH',
        help="Create sample configuration file at PATH and exit"
    )
    
    # 2. Complex custom Action (FilesSpec) - dataclass-args can't handle this
    parser.add_argument(
        '-f', '--files',
        nargs='+',  # Accept 1-2 arguments per invocation
        action=FilesSpec,
        metavar=('FILE_GLOB', 'MIMETYPE'),
        dest='files',
        help="File(s) to upload: FILE_GLOB [MIMETYPE] (repeatable)"
    )
    
    # 3. Excluded field needing short alias
    parser.add_argument(
        '-t', '--tool-configs-dir',
        type=str,
        dest='tool_configs_dir',
        help="Directory containing tool configuration files"
    )
    
    # 4. Let dataclass-args handle everything else from YacbaConfig annotations
    builder = GenericConfigBuilder(
        YacbaConfig
    )
    
    # Add all dataclass-args generated arguments
    builder.add_arguments(parser)
    
    # Parse and return
    return parser.parse_args(args)


def validate_args(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the resolved configuration.
    
    Args:
        config: Merged configuration dictionary
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        SystemExit: On validation errors
    """
    # Validate conversation manager settings
    if config.get('conversation_manager') == 'sliding_window':
        window_size = config.get('window_size', 40)
        preserve_recent = config.get('preserve_recent', 10)
        
        if window_size <= 0:
            print(f"Error: window_size must be positive, got {window_size}")
            sys.exit(1)
            
        if preserve_recent < 0:
            print(f"Error: preserve_recent cannot be negative, got {preserve_recent}")
            sys.exit(1)
            
        if preserve_recent > window_size:
            print(f"Warning: preserve_recent ({preserve_recent}) > window_size ({window_size})")
            print(f"Setting preserve_recent = window_size")
            config['preserve_recent'] = window_size
    
    elif config.get('conversation_manager') == 'summarizing':
        summary_ratio = config.get('summary_ratio', 0.3)
        
        if not 0 < summary_ratio < 1:
            print(f"Error: summary_ratio must be between 0 and 1, got {summary_ratio}")
            sys.exit(1)
    
    # Validate max_files
    max_files = config.get('max_files', 20)
    if max_files <= 0:
        print(f"Error: max_files must be positive, got {max_files}")
        sys.exit(1)
    
    return config
