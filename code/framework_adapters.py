# framework_adapters.py
# Contains adapter classes for handling framework-specific logic and transformations.

import importlib
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from loguru import logger

from strands.models.model import Model

class FrameworkAdapter(ABC):
    """
    An abstract base class for framework adapters. Each adapter encapsulates the
    logic needed to interact with a specific model framework via strands.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def create_model(self, model_name: str, adhoc_config: Dict[str, Any]) -> Optional[Model]:
        """
        Loads the appropriate Strands model class and instantiates it.
        """
        module_name = self.config["module"]
        class_name = self.config["class"]
        model_id_param = self.config["model_id_param"]
        pre_init_hook = self.config.get("pre_init_hook")

        try:
            if pre_init_hook:
                logger.debug(f"Running pre-init hook for model '{model_name}'...")
                pre_init_hook(model=model_name)

            module = importlib.import_module(module_name)
            ModelClass = getattr(module, class_name)
            
            model_args = {model_id_param: model_name}
            model_args.update(adhoc_config)

            logger.info(f"Initializing {class_name} with ad-hoc config: {adhoc_config}")
            return ModelClass(**model_args)

        except ImportError:
            logger.error(f"Could not import {class_name} from {module_name}. Is the library installed?")
            return None
        except Exception as e:
            logger.error(f"Failed to create model instance for {class_name}: {e}")
            return None

    def adapt_system_prompt(self, system_prompt: str, initial_messages: Optional[List[Dict[str, Any]]]) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]]]:
        """
        Adapts the system prompt for models that don't support it directly.
        Returns a tuple of (new_system_prompt, new_initial_messages).
        """
        # Default behavior: Keep the system prompt as is.
        return system_prompt, initial_messages

    def adapt_content(self, content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transforms the content block format for framework-specific requirements.
        """
        # Default behavior: No transformation needed.
        return content


class BedrockFrameworkAdapter(FrameworkAdapter):
    """Adapter for AWS Bedrock, which has special requirements."""

    def adapt_system_prompt(self, system_prompt: str, initial_messages: Optional[List[Dict[str, Any]]]) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]]]:
        """
        Bedrock models don't support system prompts. This method prepends the
        system prompt to the first user message instead.
        """
        logger.warning("Bedrock model detected. Merging system prompt into the first user message.")
        
        # Create a new message list to avoid modifying the original.
        messages = list(initial_messages) if initial_messages else []
        
        system_message_content = [{"type": "text", "text": system_prompt}]
        
        if messages and messages[0].get("role") == "user":
            # Prepend the system prompt content to the existing first user message.
            messages[0]["content"] = system_message_content + messages[0].get("content", [])
        else:
            # Create a new user message containing the system prompt.
            messages.insert(0, {"role": "user", "content": system_message_content})
            
        return None, messages

    def adapt_content(self, content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transforms content blocks into the format required by Bedrock,
        which does not use the 'type' key.
        """
        logger.debug("Transforming content blocks for Bedrock-specific format.")
        transformed_list = []
        for block in content:
            if block.get("type") == "text" and "text" in block:
                transformed_list.append({"text": block["text"]})
            elif block.get("type") == "image" and "source" in block:
                transformed_list.append({"image": block["source"]})
            else:
                transformed_list.append(block)
        return transformed_list

# Default adapter for frameworks that follow the standard pattern.
DefaultFrameworkAdapter = FrameworkAdapter
