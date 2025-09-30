"""
Model and framework-related type definitions for YACBA.

YACBA only manages model CONFIGURATION and framework selection.
All model interaction is handled by strands-agents.
"""

from typing import Dict, List, Any, Optional, Protocol, runtime_checkable, Literal
from typing_extensions import TypedDict
from .base import JSONDict
from .content import Message

# Framework types that YACBA needs to distinguish
FrameworkName = Literal["litellm", "openai", "anthropic", "bedrock"]

# Protocol for model objects (what strands provides to YACBA)
@runtime_checkable
class Model(Protocol):
    """
    Protocol for model objects that strands-agents provides.
    YACBA doesn't need to know implementation details.
    """
    pass  # YACBA just passes this to strands Agent

# Protocol for framework adapters (what YACBA manages)
@runtime_checkable
class FrameworkAdapter(Protocol):
    """
    Protocol for framework adapters that YACBA manages.
    These handle framework-specific configuration and content transformation.
    """

    @property
    def expected_exceptions(self) -> tuple[type[Exception], ...]:
        """Expected exception types for this framework."""
        ...

    def prepare_agent_args(
        self,
        system_prompt: str,
        messages: List[Message],
        startup_files_content: Optional[List[Message]],
        emulate_system_prompt: bool = False
    ) -> Dict[str, Any]:
        """Prepare arguments for agent initialization."""
        ...

    def transform_content(self, content: Any) -> Any:
        """Transform content for framework compatibility."""
        ...

    def adapt_tools(self, tools: List[Any], model_string: str) -> List[Any]:
        """Adapt tools for framework compatibility."""
        ...

# Model loading result (what YACBA cares about)


class ModelLoadResult(TypedDict):
    """Result of model loading operation."""
    model: Optional[Model]
    adapter: Optional[FrameworkAdapter]
    error: Optional[str]

# Protocol for agent objects (what strands provides to YACBA)
@runtime_checkable
class Agent(Protocol):
    """
    Protocol for agent objects that strands-agents provides.
    YACBA only needs to know about message history and streaming.
    """
    messages: List[Message]

    def stream_async(self, message: Any) -> Any:
        """Stream agent response - YACBA doesn't need to know details."""
        ...
