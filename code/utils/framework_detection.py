# Framework guessing rules with type safety
from typing import List, Tuple
from yacba_types.models import FrameworkName
from loguru import logger

FRAMEWORK_GUESSING_RULES: List[Tuple[str, FrameworkName]] = [
    ("gpt-", "openai"),
    ("claude", "anthropic"),
    ("gemini", "litellm"),
    ("google", "litellm"),
    ("/", "litellm"),  # Convention for litellm models like 'ollama/llama2'
]

def guess_framework_from_model_string(model_name: str) -> FrameworkName:
    """
    Makes a best guess for the model framework based on a list of rules.

    Args:
        model_name: The model name to analyze

    Returns:
        The guessed framework name
    """
    if not model_name:
        logger.warning("Empty model name provided. Defaulting to 'litellm'.")
        return "litellm"

    model_lower = model_name.lower()
    for condition, framework in FRAMEWORK_GUESSING_RULES:
        if condition in model_lower:
            logger.debug(f"Guessed '{framework}' framework for model '{model_name}' based on rule '{condition}'.")
            return framework

    # Default fallback if no rules match
    logger.warning(f"Could not determine framework for '{model_name}' based on rules. Defaulting to 'litellm'.")
    return "litellm"
