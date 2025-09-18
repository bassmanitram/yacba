# model_loader.py
# Handles the dynamic loading and instantiation of different Strands model classes.

import litellm
from typing import Dict, Any, Optional, Tuple
from loguru import logger

from strands.models.model import Model
from utils import guess_framework_from_model_string
from framework_adapters import DefaultFrameworkAdapter, BedrockFrameworkAdapter, FrameworkAdapter

class StrandsModelLoader:
    """A factory class for creating Strands Model instances using framework adapters."""

    # This dictionary now maps framework names to adapter classes and their configs.
    FRAMEWORK_ADAPTER_MAP = {
        "litellm": (DefaultFrameworkAdapter, {
            "module": "strands.models.litellm", "class": "LiteLLMModel",
            "model_id_param": "model_id", "pre_init_hook": litellm.validate_environment
        }),
        "openai": (DefaultFrameworkAdapter, {
            "module": "strands.models.openai", "class": "OpenAIModel", "model_id_param": "model"
        }),
        "anthropic": (DefaultFrameworkAdapter, {
            "module": "strands.models.anthropic", "class": "AnthropicModel", "model_id_param": "model"
        }),
        "bedrock": (BedrockFrameworkAdapter, {
            "module": "strands.models.bedrock", "class": "BedrockModel", "model_id_param": "model_id"
        })
    }

    def create_model(self, model_string: str, adhoc_config: Optional[Dict[str, Any]] = None) -> Optional[Tuple[Model, FrameworkAdapter]]:
        """
        Selects the correct framework adapter and uses it to create a model instance.
        Returns the model and the adapter instance.
        """
        adhoc_config = adhoc_config or {}
        
        if ":" in model_string:
            framework, model_name = model_string.split(":", 1)
        else:
            model_name = model_string
            framework = guess_framework_from_model_string(model_name)
            logger.info(f"Framework not specified, guessing '{framework}' for model '{model_name}'.")

        adapter_info = self.FRAMEWORK_ADAPTER_MAP.get(framework)
        if not adapter_info:
            logger.error(f"Unsupported model framework: '{framework}'")
            return None

        AdapterClass, config = adapter_info
        adapter = AdapterClass(config)
        
        logger.info(f"Attempting to load model '{model_name}' using adapter '{AdapterClass.__name__}'.")
        
        model_instance = adapter.create_model(model_name, adhoc_config)
        
        return (model_instance, adapter) if model_instance else None

