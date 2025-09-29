"""
Model configuration parsing utilities for YACBA.

Handles parsing of model configuration files and command-line overrides,
including support for nested property paths and automatic type inference.
"""

import yaml
import re
from pathlib import Path
from typing import Dict, Any, List, Union, Optional
from loguru import logger
from utils.file_utils import load_structured_file


class ModelConfigError(Exception):
    """Custom exception for model configuration errors."""
    pass


class ModelConfigParser:
    """
    Parser for model configuration files and command-line overrides.

    Supports:
    - YAML file loading
    - Property path parsing (dot notation and array indexing)
    - Automatic type inference
    - Configuration merging
    """

    @staticmethod
    def load_config_file(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load model configuration from a YAML file.

        Args:
            file_path: Path to the YAML configuration file

        Returns:
            Dictionary containing the configuration

        Raises:
            ModelConfigError: If file cannot be loaded or parsed
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise ModelConfigError(f"Model config file not found: {file_path}")

            if not path.is_file():
                raise ModelConfigError(f"Model config path is not a file: {file_path}")

            config = load_structured_file(path, 'yaml')

            if not isinstance(config, dict):
                raise ModelConfigError(f"Model config file must contain a YAML object, got {type(config).__name__}")

            logger.debug(f"Loaded model config from {file_path}: {len(config)} properties")
            return config

        except yaml.YAMLError as e:
            raise ModelConfigError(f"Invalid YAML in model config file {file_path}: {e}")
        except Exception as e:
            raise ModelConfigError(f"Error loading model config file {file_path}: {e}")

    @staticmethod
    def parse_property_override(property_override: str) -> tuple[str, Any]:
        """
        Parse a property override string in the format "path: value".

        Args:
            property_override: String in format "property.path: value"

        Returns:
            Tuple of (property_path, parsed_value)

        Raises:
            ModelConfigError: If the override format is invalid
        """
        if ':' not in property_override:
            raise ModelConfigError(
                f"Invalid property override format: '{property_override}'. "
                "Expected format: 'property.path: value'"
            )

        # Split on first colon to handle values that contain colons
        path, value_str = property_override.split(':', 1)
        path = path.strip()
        value_str = value_str.strip()

        if not path:
            raise ModelConfigError(f"Empty property path in override: '{property_override}'")

        # Parse and infer type of the value
        try:
            parsed_value = ModelConfigParser._infer_type(value_str)
            logger.debug(f"Parsed override: {path} = {parsed_value} ({type(parsed_value).__name__})")
            return path, parsed_value
        except Exception as e:
            raise ModelConfigError(f"Error parsing value '{value_str}' for property '{path}': {e}")

    @staticmethod
    def _infer_type(value_str: str) -> Any:
        """
        Infer the type of a string value and convert it appropriately.

        Args:
            value_str: String value to convert

        Returns:
            Converted value with appropriate type
        """
        value_str = value_str.strip()

        # Handle empty strings
        if not value_str:
            return ""

        # Handle quoted strings (preserve as string)
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]  # Remove quotes

        # Handle booleans
        if value_str.lower() == 'true':
            return True
        elif value_str.lower() == 'false':
            return False

        # Handle null/None
        if value_str.lower() in ('null', 'none'):
            return None

        # Handle YAML arrays and objects
        if value_str.startswith('[') or value_str.startswith('{'):
            try:
                return yaml.safe_load(value_str)
            except yaml.YAMLError:
                # If YAML parsing fails, treat as string
                return value_str

        # Handle numbers
        try:
            # Try integer first
            if '.' not in value_str and 'e' not in value_str.lower():
                return int(value_str)
            else:
                return float(value_str)
        except ValueError:
            pass

        # Default to string
        return value_str

    @staticmethod
    def apply_property_override(config: Dict[str, Any], property_path: str, value: Any) -> None:
        """
        Apply a property override to a configuration dictionary using dot notation and array indexing.

        Args:
            config: Configuration dictionary to modify
            property_path: Property path (e.g., "response_format.type" or "safety_settings[0].category")
            value: Value to set

        Raises:
            ModelConfigError: If the property path is invalid
        """
        try:
            # Parse the property path into components
            components = ModelConfigParser._parse_property_path(property_path)

            # Navigate to the parent object
            current = config
            for component in components[:-1]:
                if isinstance(component, str):
                    # Dictionary key
                    if component not in current:
                        current[component] = {}
                    current = current[component]
                elif isinstance(component, int):
                    # Array index
                    if not isinstance(current, list):
                        raise ModelConfigError(f"Cannot index non-list with [{component}] in path: {property_path}")

                    # Extend list if necessary
                    while len(current) <= component:
                        current.append({})

                    current = current[component]

            # Set the final value
            final_component = components[-1]
            if isinstance(final_component, str):
                current[final_component] = value
            elif isinstance(final_component, int):
                if not isinstance(current, list):
                    raise ModelConfigError(f"Cannot index non-list with [{final_component}] in path: {property_path}")

                # Extend list if necessary
                while len(current) <= final_component:
                    current.append(None)

                current[final_component] = value

        except Exception as e:
            raise ModelConfigError(f"Error applying override '{property_path}: {value}': {e}")

    @staticmethod
    def _parse_property_path(property_path: str) -> List[Union[str, int]]:
        """
        Parse a property path into components, handling dot notation and array indexing.

        Examples:
            "temperature" -> ["temperature"]
            "response_format.type" -> ["response_format", "type"]
            "safety_settings[0].category" -> ["safety_settings", 0, "category"]
            "stop[1]" -> ["stop", 1]

        Args:
            property_path: Property path string

        Returns:
            List of path components (strings for keys, integers for array indices)
        """
        components = []

        # Split by dots, but handle array indexing
        parts = property_path.split('.')

        for part in parts:
            # Check if this part contains array indexing
            if '[' in part and ']' in part:
                # Extract the base name and indices
                match = re.match(r'^([^[]+)(\[[^\]]+\])+$', part)
                if not match:
                    raise ModelConfigError(f"Invalid array notation in property path: {part}")

                base_name = match.group(1)
                components.append(base_name)

                # Extract all array indices
                indices = re.findall(r'\[([^\]]+)\]', part)
                for index_str in indices:
                    try:
                        index = int(index_str)
                        components.append(index)
                    except ValueError:
                        raise ModelConfigError(f"Invalid array index '{index_str}' in property path: {part}")
            else:
                components.append(part)

        return components

    @staticmethod
    def merge_configs(base_config: Dict[str, Any], overrides: List[str]) -> Dict[str, Any]:
        """
        Merge a base configuration with a list of property overrides.

        Args:
            base_config: Base configuration dictionary
            overrides: List of property override strings

        Returns:
            Merged configuration dictionary

        Raises:
            ModelConfigError: If any override is invalid
        """
        # Create a deep copy of the base config using YAML serialization
        merged_config = yaml.safe_load(yaml.dump(base_config))

        # Apply each override
        for override in overrides:
            property_path, value = ModelConfigParser.parse_property_override(override)
            ModelConfigParser.apply_property_override(merged_config, property_path, value)

        logger.debug(f"Merged config with {len(overrides)} overrides")
        return merged_config

    @staticmethod
    def validate_model_config(config: Dict[str, Any]) -> None:
        """
        Validate a model configuration dictionary.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ModelConfigError: If configuration is invalid
        """
        if not isinstance(config, dict):
            raise ModelConfigError(f"Model configuration must be a dictionary, got {type(config).__name__}")

        # Basic validation - ensure all values are YAML-serializable
        try:
            yaml.dump(config)
        except yaml.YAMLError as e:
            raise ModelConfigError(f"Model configuration contains non-serializable values: {e}")

        logger.debug(f"Validated model config with {len(config)} properties")


def parse_model_config(config_file: Optional[str] = None,
                      overrides: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Parse model configuration from file and/or command-line overrides.

    Args:
        config_file: Optional path to YAML configuration file
        overrides: Optional list of property override strings

    Returns:
        Parsed and merged configuration dictionary

    Raises:
        ModelConfigError: If configuration is invalid
    """
    parser = ModelConfigParser()

    # Start with empty config or load from file
    if config_file:
        base_config = parser.load_config_file(config_file)
    else:
        base_config = {}

    # Apply overrides if provided
    if overrides:
        merged_config = parser.merge_configs(base_config, overrides)
    else:
        merged_config = base_config

    # Validate the final configuration
    parser.validate_model_config(merged_config)

    return merged_config
