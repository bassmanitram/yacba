"""
Adapters for integrating strands_agent_factory with YACBA.

This module provides the glue code to convert YACBA's configuration
and architecture to work with strands_agent_factory components.
"""

from .config_converter import YacbaToStrandsConfigConverter

__all__ = ["YacbaToStrandsConfigConverter"]
