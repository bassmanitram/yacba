"""
Configuration subsystem for YACBA.

This module provides a unified interface to YACBA's configuration system,
including file-based configuration, CLI argument parsing, and profile management.

Main entry points:
- parse_config(): Complete configuration parsing and resolution
- YacbaConfig: Configuration dataclass
- ConfigManager: Configuration file management

The configuration system has been streamlined to eliminate duplication
and provides a single source of truth for all argument definitions.
"""

# Main interfaces from streamlined system
from .orchestrator import parse_config
from .dataclass import YacbaConfig
from .file_loader import ConfigManager

# Backward compatibility aliases
from .orchestrator import orchestrate_config_parsing
from .dataclass import YacbaConfig as Config

# Export public API
__all__ = [
    'parse_config',
    'YacbaConfig',
    'ConfigManager',
    # Backward compatibility
    'orchestrate_config_parsing',
    'Config'
]
