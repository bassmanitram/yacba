"""
Adapter modules for YACBA.

This package contains adapters that handle framework-specific and tool-specific
logic, allowing YACBA to work with different model providers and tool systems
while maintaining a consistent interface.

Structure:
- framework/: Adapters for different model frameworks (OpenAI, Anthropic, Bedrock, etc.)
- tools/: Adapters for different tool systems (MCP, Python modules, etc.)
"""

# Import the main factory functions for easy access
from .framework import get_framework_adapter
from .tools import ToolFactory

# Import commonly used adapter classes
from .framework.base_adapter import DefaultAdapter
from .framework.bedrock_adapter import BedrockAdapter
from .tools.base_adapter import ToolAdapter

__all__ = [
    # Factory functions
    'get_framework_adapter',
    'ToolFactory',
    
    # Framework adapters
    'DefaultAdapter',
    'BedrockAdapter',
    
    # Tool adapter base
    'ToolAdapter',
]

# Version info for adapter compatibility
__version__ = '1.0.0'

# Supported framework types (for validation)
SUPPORTED_FRAMEWORKS = ['litellm', 'openai', 'anthropic', 'bedrock']

# Supported tool types (for validation)  
SUPPORTED_TOOL_TYPES = ['mcp', 'python']
