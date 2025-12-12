"""
Default values and environment variable mappings for YACBA.

This module provides:
- ARGUMENT_DEFAULTS: Fallback values for YACBA configuration (nested structure)
- ARGUMENTS_FROM_ENV_VARS: Environment variable integration (YACBA_* prefix)

With cli_nested, defaults come from:
- AgentFactoryConfig (from strands-agent-factory)
- YacbaREPLConfig (YACBA-specific fields)

Environment variables use YACBA_AGENT_* and YACBA_REPL_* prefixes for nested structure.
"""

from os import environ
from typing import Dict, Any, Optional


# ============================================================================
# Default Values (Nested Structure)
# ============================================================================

ARGUMENT_DEFAULTS: Dict[str, Any] = {
    "agent": {
        # AgentFactoryConfig defaults are defined in strands-agent-factory
        # Only specify overrides if needed
        "agent_id": "yacba_agent"
    },
    "repl": {
        # YacbaREPLConfig defaults
        "headless": False,
        "cli_prompt": None,
        "max_files": 20,
    },
}


# ============================================================================
# Environment Variable Integration
# ============================================================================


def _get_env_var(section: str, key: str) -> Optional[str]:
    """
    Get environment variable with YACBA_SECTION_KEY format.

    Args:
        section: Configuration section (agent, repl)
        key: Configuration key name

    Returns:
        Environment variable value or None
        
    Examples:
        _get_env_var("agent", "model") checks for YACBA_AGENT_MODEL
        _get_env_var("repl", "headless") checks for YACBA_REPL_HEADLESS
    """
    env_key = f"YACBA_{section.upper()}_{key.upper()}"
    return environ.get(env_key)


def _build_env_vars() -> Dict[str, Any]:
    """
    Build dictionary of environment variable overrides using nested structure.

    Checks for YACBA_AGENT_* and YACBA_REPL_* environment variables.
    
    Examples:
        YACBA_AGENT_MODEL="gpt-4" → {"agent": {"model": "gpt-4"}}
        YACBA_REPL_HEADLESS="true" → {"repl": {"headless": True}}

    Returns:
        Dictionary of environment variable overrides (nested structure)
    """
    env_vars: Dict[str, Dict[str, Any]] = {"agent": {}, "repl": {}}

    # Agent fields that can be set via environment
    agent_str_keys = [
        "model",
        "session_id",
        "system_prompt",
        "initial_message",
        "agent_id",
        "summarization_model",
        "custom_summarization_prompt",
        "response_prefix",
    ]
    
    agent_int_keys = [
        "sliding_window_size",
        "preserve_recent_messages",
    ]
    
    agent_float_keys = [
        "summary_ratio",
    ]
    
    agent_bool_keys = [
        "should_truncate_results",
        "emulate_system_prompt",
        "disable_context_repair",
        "show_tool_use",
    ]

    # REPL fields that can be set via environment
    repl_str_keys = ["cli_prompt"]
    repl_int_keys = ["max_files"]
    repl_bool_keys = ["headless"]

    # Process agent fields
    for key in agent_str_keys:
        value = _get_env_var("agent", key)
        if value is not None:
            env_vars["agent"][key] = value

    for key in agent_int_keys:
        value = _get_env_var("agent", key)
        if value is not None:
            try:
                env_vars["agent"][key] = int(value)
            except ValueError:
                pass  # Skip invalid values

    for key in agent_float_keys:
        value = _get_env_var("agent", key)
        if value is not None:
            try:
                env_vars["agent"][key] = float(value)
            except ValueError:
                pass  # Skip invalid values

    for key in agent_bool_keys:
        value = _get_env_var("agent", key)
        if value is not None:
            env_vars["agent"][key] = value.lower() in ("true", "1", "yes", "on")

    # Process REPL fields
    for key in repl_str_keys:
        value = _get_env_var("repl", key)
        if value is not None:
            env_vars["repl"][key] = value

    for key in repl_int_keys:
        value = _get_env_var("repl", key)
        if value is not None:
            try:
                env_vars["repl"][key] = int(value)
            except ValueError:
                pass  # Skip invalid values

    for key in repl_bool_keys:
        value = _get_env_var("repl", key)
        if value is not None:
            env_vars["repl"][key] = value.lower() in ("true", "1", "yes", "on")

    # Remove empty sections
    if not env_vars["agent"]:
        del env_vars["agent"]
    if not env_vars["repl"]:
        del env_vars["repl"]

    return env_vars


# Build on module load
ARGUMENTS_FROM_ENV_VARS: Dict[str, Any] = _build_env_vars()
