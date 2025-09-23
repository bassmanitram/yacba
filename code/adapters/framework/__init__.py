# adapters/framework/__init__.py
"""Framework adapters for different model providers."""

from .base_adapter import DefaultAdapter
from .bedrock_adapter import BedrockAdapter
from .factory import get_framework_adapter

__all__ = ['DefaultAdapter', 'BedrockAdapter', 'get_framework_adapter']
