"""
YACBA Core Components

This module contains the core business logic components of YACBA:
- Engine: Core agent orchestration
- Manager: Resource lifecycle management  
- Agent: Strands-specific agent implementation
- Config: Configuration management and parsing
- Session: Session persistence and delegation
- Model Loading: Framework-agnostic model loading
- Callbacks: Agent interaction callbacks

These components are framework-aware but UI-agnostic.
"""

# Import main classes for easy access
from .engine import YacbaEngine
from .manager import ChatbotManager
from .agent import YacbaAgent
from .config import YacbaConfig
from .config_parser import parse_config
from .model_loader import StrandsModelLoader
from .callback_handler import YacbaCallbackHandler
from .session import DelegatingSession

__all__ = [
    # Core orchestration
    'YacbaEngine',
    'ChatbotManager',
    'YacbaAgent',
    
    # Configuration
    'YacbaConfig', 
    'parse_config',
    
    # Supporting components
    'StrandsModelLoader',
    'YacbaCallbackHandler',
    'DelegatingSession',
]

# Version info
__version__ = '1.0.0'