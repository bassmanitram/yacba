"""
CLI package for YACBA.

This package contains all command-line interface related functionality:
- User interface components (messages, completion, sessions)
- Execution modes (interactive and headless)
- Meta-command handlers
"""

from .async_repl import run_async_repl
from .headless import run_headless

__all__ = [
    # Execution modes
    'run_async_repl',
    'run_headless',
]

# CLI package version
__version__ = '1.0.0'
