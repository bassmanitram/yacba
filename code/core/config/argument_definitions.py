"""
Centralized argument definitions for YACBA.

This module provides a single source of truth for all CLI arguments

It does NOT handle configuration file parsing or merging, since it is
not responsible for other forms of configuration (profiles, config files, etc).

It provides single value checkers and converters, since it defines how the
user can express configuration values.

It does not provide CROSS-value validation, since that is the responsibility
of whatever handles the whole configuration (e.g., config orchestrator).
"""

from argparse import Action, ArgumentError, ArgumentParser
from dataclasses import dataclass
import mimetypes
import os
import pathlib
import re
from typing import Any, Dict, List, Optional, Union, Callable

from utils.general_utils import clean_dict
from utils.file_utils import resolve_glob, load_file_content
from loguru import logger
from utils.framework_detection import guess_framework_from_model_string

# Utility functions for common default factories

# Character set for valid parts of a MIME type (type and subtype).
# Includes alphanumeric, dot, underscore, hyphen, and plus sign.
# Explicitly EXCLUDES the wildcard '*' and standard tspecials (like ;, /, (, ), etc.)
# This ensures it's for a *specific* MIME type, not a pattern or one with parameters.
_MT_CHARS = r"[a-zA-Z0-9._+-]"

# Regex for a "type/subtype" format where parts use specific allowed characters.
# - ^ : Start of string
# - {_VALID_MIMETYPE_PART_CHARS}+ : One or more valid characters for the 'type'
# - / : A literal forward slash separator
# - {_VALID_MIMETYPE_PART_CHARS}+ : One or more valid characters for the 'subtype'
# - $ : End of string
# - re.IGNORECASE : MIME types are case-insensitive
_BASIC_MT = re.compile(
    fr"^{_MT_CHARS}+/{_MT_CHARS}+$",
    re.IGNORECASE
)

#
# It aint pretty but its clear, and it works!
#
class CustomUsageArgumentParser(ArgumentParser):
    def format_usage(self):
        return super().format_usage().replace('[-f FILES [FILES ...]]', '[-f FILE_GLOB [MIMETYPE]]')

    def format_help(self):
        return super().format_help().replace('-f FILES [FILES ...]', '-f FILE_GLOB [MIMETYPE]').replace('--files FILES [FILES ...]', '--files FILE_GLOB [MIMETYPE]')


class FilesSpec(Action):
    """
    An argparse Action that processes up to two arguments for a given option.

    It expects the option to be defined with nargs='*' so that argparse
    collects all potential arguments into a list before this action processes them.
    """
    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        # 'values' will be a list because nargs='*' is used in add_argument.
        # This list contains all arguments provided after the option.
        print(values)
        if len(values) > 2:
            raise ArgumentError(
                self,
                f"Option '{option_string}' expects up to two arguments, but {len(values)} were provided."
            )
        if len(values) > 1:
            if not bool(_BASIC_MT.fullmatch(values[1])):
                raise ArgumentError(
                    self,
                    f"Option '{option_string}' expects the second argument to be a mimetype, but {len(values)} were provided."
                )
        files = getattr(namespace, self.dest)
        if not files:
            files = []
            setattr(namespace, self.dest, files)
        # Store the (valid) list of values in the namespace under the destination name.
        files.append(values)

def _validate_files(files_list) -> List[List[str]]:
    files = []
    for file_group in files_list:
        file_glob = file_group[0]
        mimetype = None
        if len(file_group) == 2:
            mimetype = file_group[1]
            if '/' not in mimetype or mimetype.count('/') != 1:
                logger.warn(f"{file_group}: Mimetype '{mimetype}' must be in format 'str/str'. Ignoring")
                continue
            cat, subtype = mimetype.split('/')
            if not cat or not subtype:
                logger.warn(f"{file_group}: Mimetype '{mimetype}' must be in format 'str/str'. Ignoring")
                continue

        globbed_files = resolve_glob(file_glob)
        for file in globbed_files:
            if mimetype:
                files.append((file, mimetype))
            else:
                guessed_type, _ = mimetypes.guess_type(file)
                if guessed_type:
                    files.append((file, guessed_type))
                else:
                    files.append((file, "text/plain"))
    return files


def _validate_model_string(model_str: str) -> str:
    if not model_str:
        raise ValueError("Model string cannot be empty")

    if ":" in model_str:
        framework, model = model_str.split(":", 1)
    else:
        framework = guess_framework_from_model_string(model_str)
        model = model_str
    if not framework or not model:
        raise ValueError(f"Invalid model string format: {model_str}")
    return f"{framework}:{model}"


def _validate_bool(value: Any) -> bool:
    """
    Validate that argument is either actually a bool or a string that represents a bool
    """
    if value is None:
        return False  # Default for unspecified CLI flags
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in ['true', '1', 'yes']:
            return True
        elif value.lower() in ['false', '0', 'no']:
            return False
    raise ValueError(f"Cannot convert {value} to bool")


def _validate_int(value: Any) -> int:
    try:
        return int(value)
    except Exception as e:
        raise ValueError(f"Cannot convert {value} to int: {e}")


def _validate_float(value: Any) -> float:
    try:
        return float(value)
    except Exception as e:
        raise ValueError(f"Cannot convert {value} to float: {e}")


def _validate_file_path(p):
    """Check that string represents a path to a file that exists or can be created"""
    if not isinstance(p, str):
        raise ValueError(f"Expected string path, got {type(p)}")

    path = pathlib.Path(p)

    # File already exists
    if path.is_file():
        return str(path.resolve())

    # File doesn't exist but can be created (parent directory exists)
    if path.parent.exists() and path.parent.is_dir():
        return str(path.resolve())

    # Cannot be created
    raise ValueError(f"File path '{p}' does not exist and cannot be created")


def _validate_existing_file(path_str: str) -> str:
    p = pathlib.Path(path_str)
    if not p.is_file():
        raise ValueError(f"File {path_str} does not exist")
    return str(p.resolve())


def _validate_existing_dir(path_str: str) -> str:
    p = pathlib.Path(path_str)
    if not p.is_dir():
        raise ValueError(f"Directory {path_str} does not exist")
    return str(p.resolve())


def _validate_file_or_str(file_or_str: str) -> str:
    if file_or_str.startswith("@"):
        path_str = file_or_str[1:]
        p = pathlib.Path(path_str)
        if not p.is_file():
            raise ValueError(f"File {path_str} does not exist")
        try:
            result = load_file_content(p, 'text')
            return result['content']
        except Exception as e:
            raise ValueError(f"Error reading file {path_str}: {e}")
    return file_or_str

@dataclass
class ArgumentDefinition:
    """Definition of a single CLI argument that can generate argparse config."""
    names: List[str]
    argname: str
    help: str
    argtype: Optional[type] = None
    action: Optional[str] = None
    choices: Optional[List[str]] = None
    nargs: Optional[Union[str, int]] = None
    validator: Optional[Callable[[Any], Any]] = None
    default: Optional[Any] = None

# Centralized argument definitions - SINGLE SOURCE OF TRUTH
ARGUMENTS_FROM_ENV_VARS = clean_dict({
    "model": os.environ.get("YACBA_MODEL_ID"),
    "system_prompt": os.environ.get("YACBA_SYSTEM_PROMPT"),
    "session": os.environ.get("YACBA_SESSION_NAME"),
})

# Core defaults - can be overridden by env vars, config files, or CLI args
# MUST be expressed in strings because they may come from env vars
# which are always strings
ARGUMENT_DEFAULTS = {
    "model": "litellm:gemini/gemini-2.5-flash",
    "system_prompt":("You are a general assistant with access to various tools to enhance your capabilities. "
        "You are NOT a specialized assistant dedicated to any specific tool provider."),
    "max_files": "10",
    "conversation_manager": "sliding_window",
    "window_size": "40",
    "preserve_recent": "10",
    "summary_ratio": "0.3",
    "no_truncate_results": "False",
    "headless": "False",
    "show_tool_use": "False",
    "clear_cache": "False",
}

ARGUMENT_DEFINITIONS = [
    # Core model configuration
    ArgumentDefinition(
        names=["-m", "--model"],
        help="The model to use, in <framework>:<model_id> format. Default from YACBA_MODEL_ID or litellm: gemini/gemini-2.5-flash",
        validator=_validate_model_string,
        argname="model",
    ),

    ArgumentDefinition(
        names=["--model-config"],
        help="Path to a JSON file containing model configuration (e.g., temperature, max_tokens).",
        validator=_validate_existing_file,
        argname="model_config",
    ),

    ArgumentDefinition(
        names=["-c", "--config-override"],
        help="Override model configuration property. Format: 'property.path: value'. Can be used multiple times.",
        action="append",
        argname="config_override",
    ),

    # System prompt
    ArgumentDefinition(
        names=["-s", "--system-prompt"],
        help="System prompt for the agent. Can also be set via YACBA_SYSTEM_PROMPT.",
        argname="system_prompt",
        validator=_validate_file_or_str
    ),

    ArgumentDefinition(
        names=["--emulate-system-prompt"],
        help="Emulate system prompt as user message for models that don't support system prompts.",
        argname="emulate_system_prompt",
        action="store_true",
        validator=_validate_bool
    ),

    # Tool configuration
    ArgumentDefinition(
        names=["-t", "--tool-configs-dir"],
        help="Path to directory containing tool configuration files.",
        validator=_validate_existing_dir,
        argname="tool_configs_dir",
    ),

    # File uploads
    ArgumentDefinition(
        names=["-f", "--files"],
        help="Files to upload and analyze. Can be specified multiple times.",
        nargs="+",
        action=FilesSpec,
        validator=_validate_files,
        argname="files",
    ),

    ArgumentDefinition(
        names=["--max-files"],
        help="Maximum number of files to process. Default: 10.",
        validator=_validate_int,
        argname="max_files",

    ),

    # Session management
    ArgumentDefinition(
        names=["--session"],
        help="Session name for conversation persistence.",
        argname="session",
    ),

    ArgumentDefinition(
        names=["--agent-id"],
        help="Custom agent identifier for this session.",
        argname="agent_id"
    ),

    # Conversation Management
    ArgumentDefinition(
        names=["--conversation-manager"],
        help="Conversation management strategy. 'null' disables management, 'sliding_window' keeps recent messages, 'summarizing' creates summaries of older context. Default: sliding_window.",
        choices=["null", "sliding_window", "summarizing"],
        argname="conversation_manager",
    ),

    ArgumentDefinition(
        names=["--window-size"],
        help="Maximum number of messages in sliding window mode. Default: 40.",
        validator=_validate_int,
        argname="window_size",
    ),

    ArgumentDefinition(
        names=["--preserve-recent"],
        help="Number of recent messages to always preserve in summarizing mode. Default: 10.",
        validator=_validate_int,
        argname="preserve_recent"
    ),

    ArgumentDefinition(
        names=["--summary-ratio"],
        help="Ratio of messages to summarize vs keep (0.1-0.8) in summarizing mode. Default: 0.3.",
        validator=_validate_float,
        argname="summary_ratio",
    ),

    ArgumentDefinition(
        names=["--summarization-model"],
        help="Optional separate model for summarization (e.g., 'litellm: gemini/gemini-2.5-flash' for cheaper summaries).",
        validator=_validate_model_string,
        argname="summarization_model",
    ),

    ArgumentDefinition(
        names=["--custom-summarization-prompt"],
        help="Custom system prompt for summarization. If not provided, uses built-in prompt.",
        argname="custom_summarization_prompt",
    ),

    ArgumentDefinition(
        names=["--no-truncate-results"],
        help="Disable truncation of tool results when context window is exceeded.",
        argname="no_truncate_results",
        action="store_true",
        validator=_validate_bool

    ),

    # Execution modes
    ArgumentDefinition(
        names=["-i", "--initial-message"],
        help="Initial message to send to the agent.",
        argname="initial_message",
        validator=_validate_file_or_str
    ),

    ArgumentDefinition(
        names=["-H", "--headless"],
        help="Run in headless mode (non-interactive). Requires --initial-message.",
        argname="headless",
        action="store_true",
        validator=_validate_bool
    ),

    # Output control
    ArgumentDefinition(
        names=["--show-tool-use"],
        help="Show detailed tool usage information during execution.",
        action="store_true",
        validator=_validate_bool,
        argname="show_tool_use"
    ),

    # Performance and debugging
    ArgumentDefinition(
        names=["--clear-cache"],
        help="Clear the performance cache before starting.",
        action="store_true",
        validator=_validate_bool,
        argname="clear_cache"
    ),

    # Configuration system arguments (added by integration layer)
    ArgumentDefinition(
        names=["--profile"],
        help="Use named profile from configuration file",
        argname="profile"
    ),

    ArgumentDefinition(
        names=["--config"],
        help="Path to configuration file",
        validator=_validate_existing_file,
        argname="config"
    ),

    ArgumentDefinition(
        names=["--list-profiles"],
        help="List available profiles and exit",
        action="store_true",
        validator=_validate_bool,
        argname="list_profiles"
    ),

    ArgumentDefinition(
        names=["--show-config"],
        help="Show resolved configuration and exit",
        action="store_true",
        validator=_validate_bool,
        argname="show_config"
    ),

    ArgumentDefinition(
        names=["--init-config"],
        help="Create a sample configuration file at specified path",
        validator=_validate_file_path,
        argname="init_config"
    ),
]

# Validate and convert config values based on argument definitions


def validate_args(config: Dict[str, Any]) -> Dict[str, Any]:
    for arg_def in ARGUMENT_DEFINITIONS:
        if arg_def.validator and arg_def.argname in config:
            try:
                config[arg_def.argname] = arg_def.validator(config[arg_def.argname])
            except Exception as e:
                raise ValueError(f"Invalid value for '{arg_def.argname}': {e}")
    return config


def parse_args() -> ArgumentParser:
    """
    Create argument parser with configuration file integration.

    This is similar to unified_parser but includes config file arguments.
    """
    parser = CustomUsageArgumentParser(
        description="YACBA - Yet Another ChatBot Agent",
        add_help=False  # We'll add help manually to control order
    )

    # Add configuration file arguments first
    parser.add_argument('-h', '--help', action='help', help="Show this help message and exit")

    # Add all regular arguments from definitions
    for arg_def in ARGUMENT_DEFINITIONS:
        kwargs = {'help': arg_def.help}

        if arg_def.argtype:
            kwargs['type'] = arg_def.argtype
        if arg_def.argname:
            kwargs['dest'] = arg_def.argname
        if arg_def.action:
            kwargs['action'] = arg_def.action
        if arg_def.choices:
            kwargs['choices'] = arg_def.choices
        if arg_def.nargs:
            kwargs['nargs'] = arg_def.nargs
        if arg_def.default:
            kwargs['default'] = arg_def.default

        parser.add_argument(*arg_def.names, **kwargs)

    return parser.parse_args()
