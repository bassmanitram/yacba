"""
Type definitions for YACBA.

This module provides type definitions focused on YACBA's core responsibilities:
- Configuration management
- File processing
- Session persistence
- Framework orchestration

Tool execution and protocol details are handled by strands-agents.
"""

# Import all from submodules
from .base import JSONValue, JSONDict, PathLike
from .config import ModelConfig, ToolConfig, MCPToolConfig, PythonToolConfig
from .config import ToolDiscoveryResult, SessionData, FileUpload
from .content import ContentBlock, TextBlock, ImageBlock, MessageContent
from .content import Message
from .tools import Tool, ToolLoadResult, ToolCreationResult
from .models import FrameworkName, Model, FrameworkAdapter, ModelLoadResult
from .models import Agent, SessionLike

__all__ = [
    # Base types
    'JSONValue',
    'JSONDict',
    'PathLike',

    # Config types (what YACBA manages)
    'ModelConfig',
    'ToolConfig',
    'MCPToolConfig',
    'PythonToolConfig',
    'ToolDiscoveryResult',  # Added this
    'SessionData',
    'FileUpload',

    # Content types (what YACBA processes)
    'ContentBlock',
    'TextBlock',
    'ImageBlock',
    'MessageContent',
    'Message',

    # Tool types (what YACBA configures, not executes)
    'Tool',
    'ToolLoadResult',
    'ToolCreationResult',

    # Model types (what YACBA orchestrates)
    'FrameworkName',
    'Model',
    'FrameworkAdapter',
    'ModelLoadResult',
    'Agent',
    'SessionLike',
]
