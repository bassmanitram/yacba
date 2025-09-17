# model_loader.py
# A factory for creating Strands model instances from different frameworks.

from typing import Dict, Any, Optional
from loguru import logger

# Import the base class for type hinting.
from strands.models.model import Model
from utils import guess_framework_from_model_string

class StrandsModelLoader:
    """
    A factory class that instantiates the correct Strands Model class based on a
    provided model string in the format <framework>:<model_id>.
    """
    def create_model(self, model_string: str, model_config: Dict[str, Any]) -> Optional[Model]:
        """
        Parses the model string and instantiates the appropriate model class.

        Args:
            model_string: The model identifier, e.g., "litellm:gemini/gemini-pro" or just "gpt-4o".
            model_config: A dictionary of ad-hoc arguments for the model constructor.

        Returns:
            An instance of a Strands Model class, or None if creation fails.
        """
        if ':' in model_string:
            framework, model_name = model_string.split(':', 1)
        else:
            # If no framework is specified, guess it.
            model_name = model_string
            framework = guess_framework_from_model_string(model_name)

        logger.info(f"Attempting to load model '{model_name}' using framework '{framework}'.")

        try:
            if framework == "litellm":
                from strands.models.litellm import LiteLLMModel
                import litellm
                litellm.validate_environment(model=model_name)
                logger.info(f"Initializing LiteLLMModel with ad-hoc config: {model_config}")
                return LiteLLMModel(model_id=model_name, **model_config)

            elif framework == "openai":
                # Placeholder for OpenAI integration
                logger.warning("OpenAI model framework is not yet implemented.")
                # from strands.models.openai import OpenAIModel
                # return OpenAIModel(model=model_name, **model_config)
                return None
                
            elif framework == "anthropic":
                # Placeholder for Anthropic integration
                logger.warning("Anthropic model framework is not yet implemented.")
                # from strands.models.anthropic import AnthropicModel
                # return AnthropicModel(model=model_name, **model_config)
                return None

            elif framework == "bedrock":
                # Placeholder for Bedrock integration
                logger.warning("Bedrock model framework is not yet implemented.")
                # from strands.models.bedrock import BedrockModel
                # return BedrockModel(model=model_name, **model_config)
                return None

            else:
                logger.error(f"Unsupported model framework: '{framework}'")
                return None
        except ImportError:
            logger.error(f"Could not import dependencies for the '{framework}' framework. Please ensure it is installed.")
            return None
        except Exception as e:
            logger.error(f"Failed to instantiate model '{model_name}' from framework '{framework}': {e}")
            return None
