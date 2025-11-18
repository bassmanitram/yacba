"""
Configuration subsystem for YACBA.

This module provides a unified interface to YACBA's configuration system,
including file-based configuration (via profile-config), CLI argument parsing,
and profile management.

Main entry points:
- parse_config(): Complete configuration parsing and resolution
- YacbaConfig: Configuration dataclass

The configuration system has been streamlined to eliminate duplication
and provides a single source of truth for all argument definitions.
"""

# Main interfaces from streamlined system
from .factory import parse_config
from .dataclass import YacbaConfig

# Backward compatibility aliases
from .dataclass import YacbaConfig as Config

# Export public API
__all__ = [
    "parse_config",
    "YacbaConfig",
    # Backward compatibility
    "Config",
]
