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
from .base import JSONValue, JSONDict, PathLike, ExitCode
from .config import ToolConfig, MCPToolConfig, PythonToolConfig
from .config import ToolDiscoveryResult, SessionData, FileUpload
from .content import ContentBlock, TextBlock, ImageBlock, MessageContent
from .content import Message

__all__ = [
    # Base types
    'JSONValue',
    'JSONDict',
    'PathLike',
    'ExitCode',

    # Config types (what YACBA manages)
    'ToolConfig',
    'MCPToolConfig',
    'PythonToolConfig',
    'ToolDiscoveryResult',
    'SessionData',
    'FileUpload',

    # Content types (what YACBA processes)
    'ContentBlock',
    'TextBlock',
    'ImageBlock',
    'MessageContent',
    'Message',
]