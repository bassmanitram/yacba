# model_loader.py
# Handles the dynamic loading and instantiation of different Strands model classes.

import importlib
import litellm
from typing import Dict, Any, Optional, Tuple
from loguru import logger

from strands.models.model import Model
from utils.framework_detection import guess_framework_from_model_string
from framework_adapters import DefaultAdapter, BedrockAdapter, FrameworkAdapter

class StrandsModelLoader:
    """A factory class for creating Strands Model instances."""

    FRAMEWORK_HANDLERS = {
        "litellm": {
            "module": "strands.models.litellm",
            "class": "LiteLLMModel",
            "model_id_param": "model_id",
            "pre_init_hook": litellm.validate_environment,
            "adapter": DefaultAdapter
        },
        "openai": {
            "module": "strands.models.openai",
            "class": "OpenAIModel",
            "model_id_param": "model",
            "pre_init_hook": None,
            "adapter": DefaultAdapter
        },
        "anthropic": {
            "module": "strands.models.anthropic",
            "class": "AnthropicModel",
            "model_id_param": "model",
            "pre_init_hook": None,
            "adapter": DefaultAdapter
        },
        "bedrock": {
            "module": "strands.models.bedrock",
            "class": "BedrockModel",
            "model_id_param": "model_id",
            "pre_init_hook": None,
            "adapter": BedrockAdapter
        }
    }

    def create_model(self, model_string: str, adhoc_config: Optional[Dict[str, Any]] = None) -> Optional[Tuple[Model, FrameworkAdapter]]:
        """
        Parses a model string, loads the appropriate Strands model class,
        and instantiates it with the provided configuration.
        Returns the model instance and the appropriate framework adapter.
        """
        adhoc_config = adhoc_config or {}
        
        if ":" in model_string:
            framework, model_name = model_string.split(":", 1)
        else:
            model_name = model_string
            framework = guess_framework_from_model_string(model_name)
            logger.info(f"Framework not specified, guessing '{framework}' for model '{model_name}'.")

        handler = self.FRAMEWORK_HANDLERS.get(framework)
        if not handler:
            logger.error(f"Unsupported model framework: '{framework}'")
            return None, None

        logger.info(f"Attempting to load model '{model_name}' using framework '{framework}'.")
        AdapterClass = handler["adapter"]

        try:
            if handler["pre_init_hook"]:
                logger.debug(f"Running pre-init hook for {framework}...")
                handler["pre_init_hook"](model=model_name)

            module = importlib.import_module(handler["module"])
            ModelClass = getattr(module, handler["class"])
            
            model_args = {handler["model_id_param"]: model_name}
            model_args.update(adhoc_config)

            logger.info(f"Initializing {handler['class']} with ad-hoc config: {adhoc_config}")
            model_instance = ModelClass(**model_args)
            return model_instance, AdapterClass()

        except ImportError:
            logger.error(f"Could not import {handler['class']} from {handler['module']}. Is the library installed?")
            return None, None
        except Exception as e:
            logger.error(f"Failed to create model instance for framework '{framework}': {e}")
            return None, None
