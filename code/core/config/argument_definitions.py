"""
Centralized argument definitions for YACBA.

This module provides a single source of truth for all CLI arguments,
dataclass fields, and configuration mappings. It eliminates the need to 
maintain argument definitions in multiple places by auto-generating
both argparse configurations and dataclass field definitions.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Callable
from pathlib import Path


@dataclass
class ArgumentDefinition:
    """Definition of a single CLI argument that can generate both argparse config and dataclass fields."""
    
    # Argument names (first is primary, rest are aliases)
    names: List[str]
    
    # Argparse configuration
    help: str
    argtype: Optional[type] = None
    action: Optional[str] = None
    default: Any = None
    choices: Optional[List[str]] = None
    nargs: Optional[Union[str, int]] = None
    required: bool = False
    
    # Configuration file integration
    config_key: Optional[str] = None  # Key in config file (defaults to primary name with underscores)
    
    # Default value resolution (for detecting CLI overrides)
    default_factory: Optional[Callable[[], Any]] = None
    
    # Validation
    validator: Optional[Callable[[Any], Any]] = None
    
    # Dataclass field configuration
    dataclass_type: Optional[type] = None  # Type for dataclass field (defaults to argtype)
    is_optional: bool = False  # Whether this should be Optional[T] in dataclass
    dataclass_default_factory: Optional[Callable] = None  # For complex defaults like lists
    
    def __post_init__(self):
        """Set derived values after initialization."""
        if self.config_key is None:
            # Convert primary name to config key format
            primary_name = self.names[0].lstrip('-').replace('-', '_')
            self.config_key = primary_name
            
        # Set dataclass_type if not explicitly provided
        if self.dataclass_type is None:
            if self.argtype:
                self.dataclass_type = self.argtype
            elif self.action == "store_true":
                self.dataclass_type = bool
            else:
                self.dataclass_type = str
    
    @property
    def primary_name(self) -> str:
        """Get the primary argument name."""
        return self.names[0]
    
    @property
    def attr_name(self) -> str:
        """Get the attribute name in the Namespace object."""
        return self.primary_name.lstrip('-').replace('-', '_')
    
    def get_default_value(self) -> Any:
        """Get the default value, using factory if available."""
        if self.default_factory:
            return self.default_factory()
        return self.default
    
    def get_dataclass_field_config(self) -> Dict[str, Any]:
        """Generate dataclass field configuration."""
        field_config = {}
        
        # Handle default values
        if self.dataclass_default_factory:
            field_config['default_factory'] = self.dataclass_default_factory
        elif self.default_factory:
            field_config['default'] = self.default_factory()
        elif self.default is not None:
            field_config['default'] = self.default
        elif self.action == "store_true":
            field_config['default'] = False
        elif self.is_optional:
            field_config['default'] = None
        
        return field_config
    
    def get_dataclass_type_annotation(self) -> str:
        """Generate type annotation string for dataclass field."""
        base_type = self.dataclass_type.__name__ if self.dataclass_type else 'str'
        
        # Handle special cases
        if self.nargs == "*":
            base_type = f"List[{base_type}]"
        elif self.action == "append":
            base_type = f"List[{base_type}]"
        
        # Handle optional types
        if self.is_optional or self.default is None:
            base_type = f"Optional[{base_type}]"
        
        return base_type


# Utility functions for common default factories
def _get_default_model() -> str:
    import os
    return os.environ.get("YACBA_MODEL_ID", "litellm:gemini/gemini-2.5-flash")

def _get_default_system_prompt() -> str:
    import os
    return os.environ.get("YACBA_SYSTEM_PROMPT", 
        "You are a general assistant with access to various tools to enhance your capabilities. "
        "You are NOT a specialized assistant dedicated to any specific tool provider.")

def _get_default_session_name() -> str:
    import os
    return os.environ.get("YACBA_SESSION_NAME", "default")


# Centralized argument definitions - SINGLE SOURCE OF TRUTH
ARGUMENT_DEFINITIONS = [
    # Core model configuration
    ArgumentDefinition(
        names=["-m", "--model"],
        help=f"The model to use, in <framework>:<model_id> format. Default from YACBA_MODEL_ID or litellm:gemini/gemini-1.5-flash",
        default_factory=_get_default_model,
        dataclass_type=str
    ),
    
    ArgumentDefinition(
        names=["--model-config"],
        help="Path to a JSON file containing model configuration (e.g., temperature, max_tokens).",
        dataclass_type=str,
        is_optional=True
    ),
    
    ArgumentDefinition(
        names=["-c", "--config-override"],
        help="Override model configuration property. Format: 'property.path:value'. Can be used multiple times.",
        action="append",
        config_key="config_overrides",
        dataclass_type=str,
        dataclass_default_factory=list
        # Fixed: Removed is_optional=True since it has dataclass_default_factory
    ),
    
    # System prompt
    ArgumentDefinition(
        names=["-s", "--system-prompt"],
        help="System prompt for the agent. Can also be set via YACBA_SYSTEM_PROMPT.",
        default_factory=_get_default_system_prompt,
        dataclass_type=str
    ),
    
    ArgumentDefinition(
        names=["--emulate-system-prompt"],
        help="Emulate system prompt as user message for models that don't support system prompts.",
        action="store_true",
        dataclass_type=bool
    ),
    
    # Tool configuration
    ArgumentDefinition(
        names=["-t", "--tool-configs-dir"],
        help="Path to directory containing tool configuration files.",
        dataclass_type=str,
        is_optional=True
    ),
    
    # File uploads
    ArgumentDefinition(
        names=["-f", "--files"],
        help="Files to upload and analyze. Can be specified multiple times.",
        nargs="*",
        default=[],
        dataclass_type=str,
        dataclass_default_factory=list
    ),
    
    ArgumentDefinition(
        names=["--max-files"],
        help="Maximum number of files to process. Default: 10.",
        argtype=int,
        default=10,
        dataclass_type=int
    ),
    
    # Session management
    ArgumentDefinition(
        names=["--session"],
        help="Session name for conversation persistence.",
        default_factory=_get_default_session_name,
        dataclass_type=str
        # Fixed: Removed is_optional=True since it has a default_factory
    ),
    
    # Conversation Management
    ArgumentDefinition(
        names=["--conversation-manager"],
        help="Conversation management strategy. 'null' disables management, 'sliding_window' keeps recent messages, 'summarizing' creates summaries of older context. Default: sliding_window.",
        choices=["null", "sliding_window", "summarizing"],
        default="sliding_window",
        dataclass_type=str
    ),
    
    ArgumentDefinition(
        names=["--window-size"],
        help="Maximum number of messages in sliding window mode. Default: 40.",
        argtype=int,
        default=40,
        dataclass_type=int
    ),
    
    ArgumentDefinition(
        names=["--preserve-recent"],
        help="Number of recent messages to always preserve in summarizing mode. Default: 10.",
        argtype=int,
        default=10,
        dataclass_type=int
    ),
    
    ArgumentDefinition(
        names=["--summary-ratio"],
        help="Ratio of messages to summarize vs keep (0.1-0.8) in summarizing mode. Default: 0.3.",
        argtype=float,
        default=0.3,
        dataclass_type=float
    ),
    
    ArgumentDefinition(
        names=["--summarization-model"],
        help="Optional separate model for summarization (e.g., 'litellm:gemini/gemini-2.5-flash' for cheaper summaries).",
        dataclass_type=str,
        is_optional=True
    ),
    
    ArgumentDefinition(
        names=["--custom-summarization-prompt"],
        help="Custom system prompt for summarization. If not provided, uses built-in prompt.",
        dataclass_type=str,
        is_optional=True
    ),
    
    ArgumentDefinition(
        names=["--no-truncate-results"],
        help="Disable truncation of tool results when context window is exceeded.",
        action="store_true",
        dataclass_type=bool
    ),
    
    # Execution modes
    ArgumentDefinition(
        names=["-i", "--initial-message"],
        help="Initial message to send to the agent.",
        dataclass_type=str,
        is_optional=True
    ),
    
    ArgumentDefinition(
        names=["-H", "--headless"],
        help="Run in headless mode (non-interactive). Requires --initial-message.",
        action="store_true",
        dataclass_type=bool
    ),
    
    # Output control
    ArgumentDefinition(
        names=["--show-tool-use"],
        help="Show detailed tool usage information during execution.",
        action="store_true",
        dataclass_type=bool
    ),
    
    ArgumentDefinition(
        names=["--agent-id"],
        help="Custom agent identifier for this session.",
        dataclass_type=str,
        is_optional=True
    ),
    
    # Performance and debugging
    ArgumentDefinition(
        names=["--clear-cache"],
        help="Clear the performance cache before starting.",
        action="store_true",
        dataclass_type=bool
    ),
    
    # Configuration system arguments (added by integration layer)
    ArgumentDefinition(
        names=["--profile"],
        help="Use named profile from configuration file",
        dataclass_type=str,
        is_optional=True
    ),
    
    ArgumentDefinition(
        names=["--config"],
        help="Path to configuration file",
        dataclass_type=str,
        is_optional=True
    ),
    
    ArgumentDefinition(
        names=["--list-profiles"],
        help="List available profiles and exit",
        action="store_true",
        dataclass_type=bool
    ),
    
    ArgumentDefinition(
        names=["--show-config"],
        help="Show resolved configuration and exit",
        action="store_true",
        dataclass_type=bool
    ),
    
    ArgumentDefinition(
        names=["--init-config"],
        help="Create sample configuration file at specified path",
        dataclass_type=str,
        is_optional=True
    ),
]

def get_argument_by_name(name: str) -> Optional[ArgumentDefinition]:
    """Get argument definition by any of its names."""
    for arg_def in ARGUMENT_DEFINITIONS:
        if name in arg_def.names:
            return arg_def
    return None


def get_argument_by_attr(attr_name: str) -> Optional[ArgumentDefinition]:
    """Get argument definition by its attribute name."""
    for arg_def in ARGUMENT_DEFINITIONS:
        if arg_def.attr_name == attr_name:
            return arg_def
    return None


def get_all_config_mappings() -> Dict[str, str]:
    """Get mapping of config keys to argument attribute names."""
    return {arg_def.config_key: arg_def.attr_name for arg_def in ARGUMENT_DEFINITIONS if arg_def.config_key}


def get_all_default_values() -> Dict[str, Any]:
    """Get all default values for arguments."""
    return {arg_def.attr_name: arg_def.get_default_value() for arg_def in ARGUMENT_DEFINITIONS}


def generate_dataclass_code() -> str:
    """Generate dataclass code from argument definitions."""
    lines = [
        '"""Auto-generated YacbaConfig dataclass from argument definitions."""',
        '',
        'from dataclasses import dataclass, field',
        'from typing import List, Optional',
        '',
        '@dataclass',
        'class YacbaConfig:',
        '    """Configuration class generated from argument definitions."""'
    ]
    
    for arg_def in ARGUMENT_DEFINITIONS:
        type_annotation = arg_def.get_dataclass_type_annotation()
        field_config = arg_def.get_dataclass_field_config()
        
        if field_config:
            if 'default_factory' in field_config:
                field_part = f"field(default_factory={field_config['default_factory'].__name__})"
            else:
                field_part = f"field(default={repr(field_config['default'])})"
        else:
            field_part = ""
        
        if field_part:
            lines.append(f"    {arg_def.attr_name}: {type_annotation} = {field_part}")
        else:
            lines.append(f"    {arg_def.attr_name}: {type_annotation}")
    
    return '\n'.join(lines)