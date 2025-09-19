"""
Handles the dynamic loading and instantiation of different Strands model classes.
Migrated to use focused type system.
"""

import importlib
import litellm
from typing import Dict, Any, Optional, Tuple, List
from loguru import logger

# Import focused types
from yacba_types.models import Model, FrameworkAdapter, FrameworkName, ModelLoadResult
from yacba_types.config import ModelConfig
from general_utils import guess_framework_from_model_string
from framework_adapters import DefaultAdapter, BedrockAdapter

class StrandsModelLoader:
    """
    A factory class for creating Strands Model instances with proper type safety.
    Focused on YACBA's responsibility: model configuration and framework selection.
    """

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

    def create_model(
        self, 
        model_string: str, 
        model_config: Optional[ModelConfig] = None
    ) -> ModelLoadResult:
        """
        Parses a model string, loads the appropriate Strands model class,
        and instantiates it with the provided configuration.
        
        Args:
            model_string: Model string in format "framework:model" or just "model"
            model_config: Optional model configuration parameters
            
        Returns:
            ModelLoadResult with model, adapter, and any error information
        """
        model_config = model_config or {}
        
        # Parse model string and determine framework
        if ":" in model_string:
            framework, model_name = model_string.split(":", 1)
        else:
            model_name = model_string
            framework = guess_framework_from_model_string(model_name)
            logger.info(f"Framework not specified, guessed '{framework}' for model '{model_name}'.")

        # Validate framework is supported
        handler = self.FRAMEWORK_HANDLERS.get(framework)
        if not handler:
            error_msg = f"Unsupported model framework: '{framework}'"
            logger.error(error_msg)
            return ModelLoadResult(
                model=None,
                adapter=None,
                error=error_msg
            )

        logger.info(f"Attempting to load model '{model_name}' using framework '{framework}'.")
        
        try:
            # Create adapter instance
            AdapterClass = handler["adapter"]
            adapter = AdapterClass()

            # Run pre-initialization hook if needed
            if handler["pre_init_hook"]:
                logger.debug(f"Running pre-init hook for {framework}...")
                handler["pre_init_hook"](model=model_name)

            # Load the model class dynamically
            module = importlib.import_module(handler["module"])
            ModelClass = getattr(module, handler["class"])
            
            # Prepare model arguments
            model_args = {handler["model_id_param"]: model_name}
            model_args.update(model_config)

            logger.info(f"Initializing {handler['class']} with config: {model_config}")
            model_instance = ModelClass(**model_args)
            
            return ModelLoadResult(
                model=model_instance,
                adapter=adapter,
                error=None
            )

        except ImportError as e:
            error_msg = f"Could not import {handler['class']} from {handler['module']}. Is the library installed? {e}"
            logger.error(error_msg)
            return ModelLoadResult(
                model=None,
                adapter=None,
                error=error_msg
            )
        except Exception as e:
            error_msg = f"Failed to create model instance for framework '{framework}': {e}"
            logger.error(error_msg)
            return ModelLoadResult(
                model=None,
                adapter=None,
                error=error_msg
            )

    def get_supported_frameworks(self) -> List[FrameworkName]:
        """
        Returns a list of supported framework names.
        
        Returns:
            List of supported framework names
        """
        return list(self.FRAMEWORK_HANDLERS.keys())  # type: ignore

    def validate_framework(self, framework: str) -> bool:
        """
        Validates if a framework is supported.
        
        Args:
            framework: Framework name to validate
            
        Returns:
            True if framework is supported, False otherwise
        """
        return framework in self.FRAMEWORK_HANDLERS
