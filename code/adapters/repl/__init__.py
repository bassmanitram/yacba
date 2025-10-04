"""
Adapters for integrating YACBA with repl_toolkit.

This module provides adapter classes that bridge between YACBA's engine
and the repl_toolkit's protocol interfaces.
"""

from .backend_adapter import YacbaAsyncBackend, YacbaHeadlessBackend
from .commands import YacbaCommandRegistry
from .completer import YacbaCompleter

__all__ = [
    "YacbaAsyncBackend",
    "YacbaHeadlessBackend", 
    "YacbaCommandRegistry",
    "YacbaCompleter",
]