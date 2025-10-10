"""
Adapters for integrating strands_agent_factory with YACBA.

This module provides the glue code to convert YACBA's configuration
and architecture to work with strands_agent_factory components.
"""

from .config_converter import YacbaToStrandsConfigConverter
from .backend_adapter import YacbaStrandsBackend

__all__ = [
    'YacbaToStrandsConfigConverter',
    'YacbaStrandsBackend'
]