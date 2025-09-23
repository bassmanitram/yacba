from typing import Any

from yacba_types.models import FrameworkAdapter
from .bedrock_adapter import BedrockAdapter
from .base_adapter import DefaultAdapter

def get_framework_adapter(model: Any) -> FrameworkAdapter:
    """
    Selects the appropriate framework adapter based on the model object's type.

    Args:
        model: The model instance from a strands library.

    Returns:
        An instance of a FrameworkAdapter.
    """
    model_class_name = model.__class__.__name__
    if "Bedrock" in model_class_name:
        return BedrockAdapter()
    # Default to the standard adapter for LiteLLM, OpenAI, Anthropic, etc.
    return DefaultAdapter()
