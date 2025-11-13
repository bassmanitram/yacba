"""
Base type definitions used throughout YACBA.
"""

from typing import (Union, Dict, List, Any, Protocol,
                    runtime_checkable)
from pathlib import Path
from enum import IntEnum
import os

# Basic JSON types
JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONDict = Dict[str, JSONValue]

# Path-like objects
PathLike = Union[str, Path, os.PathLike]


# Exit codes for the application


class ExitCode(IntEnum):
    """Standard exit codes for YACBA application."""
    SUCCESS = 0
    CONFIG_ERROR = 1
    INITIALIZATION_ERROR = 2
    RUNTIME_ERROR = 3
    INTERRUPTED = 4
    FATAL_ERROR = 5
    USER_INTERRUPT = 5


# Protocol for objects that can be converted to string
@runtime_checkable
class Stringable(Protocol):

    def __str__(self) -> str: ...


# Protocol for objects with a close method
@runtime_checkable
class Closeable(Protocol):

    def close(self) -> None: ...


# Protocol for context managers
@runtime_checkable
class ContextManager(Protocol):

    def __enter__(self): ...

    def __exit__(self, exc_type, exc_val, exc_tb): ...