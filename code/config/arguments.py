"""
Default values and environment variable mappings for YACBA.

This module provides:
- ARGUMENT_DEFAULTS: Fallback values for all configuration fields
- ARGUMENTS_FROM_ENV_VARS: Environment variable integration (YACBA_* prefix)

All CLI argument parsing is handled automatically by dataclass-args via
the YacbaConfig dataclass annotations. This module only provides defaults
and environment variable mappings that feed into the configuration resolution.
"""

from os import environ
from typing import Dict, Any, Optional


# ============================================================================
# Default Values (Fallback Only)
# ============================================================================

ARGUMENT_DEFAULTS: Dict[str, Any] = {
    # Core
    "model_string": "litellm:gemini/gemini-2.5-flash",
    "system_prompt": (
        "You are a highly capable AI assistant with access to various tools "
        "and the ability to read and analyze files. Provide helpful, accurate, "
        "and contextual responses."
    ),
    # Model configuration
    "model_config": {},
    "summarization_model_config": {},
    "emulate_system_prompt": False,
    "disable_context_repair": False,
    # File handling
    "max_files": 20,
    "tool_configs_dir": None,
    # Session management
    "session_name": None,
    "agent_id": None,
    # Conversation management
    "conversation_manager_type": "sliding_window",
    "sliding_window_size": 40,
    "preserve_recent_messages": 10,
    "summary_ratio": 0.3,
    "summarization_model": None,
    "custom_summarization_prompt": None,
    "should_truncate_results": True,
    # Execution mode
    "headless": False,
    "initial_message": None,
    # Output control
    "show_tool_use": False,
    # UI customization
    "cli_prompt": None,
    "response_prefix": None,
}


# ============================================================================
# Environment Variable Integration
# ============================================================================


def _get_env_var(key: str) -> Optional[str]:
    """
    Get environment variable with YACBA_ prefix.

    Args:
        key: Configuration key name

    Returns:
        Environment variable value or None
    """
    env_key = f"YACBA_{key.upper()}"
    return environ.get(env_key)


def _build_env_vars() -> Dict[str, Any]:
    """
    Build dictionary of environment variable overrides.

    Checks for YACBA_* environment variables for each default key.
    Only includes variables that are actually set.
    Only processes scalar values (not dicts/objects).

    Returns:
        Dictionary of environment variable overrides
    """
    env_vars = {}

    # Skip object-type configs that can't be set via environment variables
    # These must be provided via configuration files or CLI arguments
    SKIP_KEYS = {"model_config", "summarization_model_config"}

    for key in ARGUMENT_DEFAULTS.keys():
        if key in SKIP_KEYS:
            continue

        value = _get_env_var(key)
        if value is not None:
            # Type conversion for known types
            if key in ["max_files", "sliding_window_size", "preserve_recent_messages"]:
                try:
                    env_vars[key] = int(value)
                except ValueError:
                    pass  # Skip invalid values
            elif key in ["summary_ratio"]:
                try:
                    env_vars[key] = float(value)
                except ValueError:
                    pass
            elif key in [
                "headless",
                "show_tool_use",
                "emulate_system_prompt",
                "should_truncate_results",
                "disable_context_repair",
            ]:
                # Boolean conversion
                env_vars[key] = value.lower() in ("true", "1", "yes", "on")
            else:
                env_vars[key] = value

    return env_vars


# Build on module load
ARGUMENTS_FROM_ENV_VARS: Dict[str, Any] = _build_env_vars()
