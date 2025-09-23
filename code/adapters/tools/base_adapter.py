from abc import ABC, abstractmethod
from contextlib import ExitStack
from typing import Any, Dict

from yacba_types.tools import ToolCreationResult


class ToolAdapter(ABC):
    """Abstract base class for a tool adapter."""
    def __init__(self, exit_stack: ExitStack):
        self.exit_stack = exit_stack

    @abstractmethod
    def create(self, config: Dict[str, Any]) -> ToolCreationResult:
        """Creates a tool or tools based on the provided configuration."""
        pass
