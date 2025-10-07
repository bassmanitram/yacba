# model_loader.py
# Handles the dynamic loading and instantiation of different Strands model classes.

import importlib
import litellm
from typing import Dict, Any, Optional, Tuple
from loguru import logger
import re

from strands.models.model import Model
from adapters.framework.base_adapter import DefaultAdapter
from adapters.framework.bedrock_adapter import BedrockAdapter
from yacba_types.models import FrameworkAdapter
from utils.framework_detection import guess_framework_from_model_string

BEDROCK_PROFILE_ARN_RE = re.compile(r"^arn:aws[\w-]*:bedrock:[\w-]+:\d{12}:inference-profile/.+$")
BEDROCK_PROFILE_ID_RE  = re.compile(r"^(?:inference-profile/)?ip-[A-Za-z0-9\-]{6,}$")

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

    def _normalize_bedrock_target(self, model_name: str, adhoc: dict) -> tuple[dict, dict]:
        """
        Decide whether the user passed a Bedrock model_id or an Inference Profile.
        Returns (model_args_override, cleaned_adhoc).
        """
        cleaned = dict(adhoc or {})
        prof_arn = cleaned.pop("inference_profile_arn", None)
        prof_id  = cleaned.pop("inference_profile_id", None)

        if not prof_arn and not prof_id:
            if BEDROCK_PROFILE_ARN_RE.match(model_name or ""):
                prof_arn, model_name = model_name, None
            elif BEDROCK_PROFILE_ID_RE.match(model_name or ""):
                prof_id, model_name = model_name, None

        if prof_arn:
            return ({"inference_profile_arn": prof_arn}, cleaned)
        if prof_id:
            return ({"inference_profile_id": prof_id}, cleaned)

        return ({}, cleaned)

    def create_model(self, model_string: str,
                     model_config: Optional[Dict[str, Any]] = None) -> Optional[
                         Tuple[Model, FrameworkAdapter]]:
        """
        Parses a model string, loads the appropriate Strands model class,
        and instantiates it with the provided configuration.
        Returns the model instance and the appropriate framework adapter.
        """
        model_config = model_config or {}

        if ":" in model_string:
            framework, model_name = model_string.split(":", 1)
        else:
            model_name = model_string
            framework = guess_framework_from_model_string(model_name)
            logger.info(f"Framework not specified, guessing '{framework}' "
                        f"for model '{model_name}'.")

        handler = self.FRAMEWORK_HANDLERS.get(framework)
        if not handler:
            logger.error(f"Unsupported model framework: '{framework}'")
            return None, None

        logger.info(f"Attempting to load model '{model_name}' using "
                    f"framework '{framework}'.")
        AdapterClass = handler["adapter"]

        try:
            if handler["pre_init_hook"]:
                logger.debug(f"Running pre-init hook for {framework}...")
                handler["pre_init_hook"](model=model_name)

            module = importlib.import_module(handler["module"])
            ModelClass = getattr(module, handler["class"])

            model_args: Dict[str, Any] = {}

            if framework == "bedrock":
                overrides, cleaned = self._normalize_bedrock_target(model_name, adhoc_config)
                adhoc_config = cleaned

                if overrides:
                    logger.info(f"Using Bedrock Inference Profile ({'arn' if 'inference_profile_arn' in overrides else 'id'})")
                    model_args.update(overrides)
                else:
                    model_args[handler["model_id_param"]] = model_name
            else:
                model_args[handler["model_id_param"]] = model_name

            model_args = {handler["model_id_param"]: model_name}
            model_args.update(model_config)

            logger.info(f"Initializing {handler['class']} with ad-hoc "
                        f"config: {model_config}")
            model_instance = ModelClass(**model_args)
            return model_instance, AdapterClass()

        except ImportError:
            logger.error(f"Could not import {handler['class']} from "
                         f"{handler['module']}. Is the library installed?")
            return None, None
        except Exception as e:
            logger.error("Failed to create model instance for framework "
                         f"'{framework}': {e}")
            return None, None
