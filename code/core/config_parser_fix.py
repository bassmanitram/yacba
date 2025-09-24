# Fix for the _create_model_config function in core/config_parser.py
# Replace the existing function with this corrected version:

def _create_model_config(model_string: str, config_file: Optional[str] = None, 
                        config_overrides: Optional[List[str]] = None) -> ModelConfig:
    """
    Create a ModelConfig object from the model string and additional parameters.
    
    Args:
        model_string: The model string in format 'framework:model'
        config_file: Optional path to model configuration JSON file
        config_overrides: Optional list of configuration overrides
        
    Returns:
        ModelConfig object
    """
    # Parse framework and model from string
    if ":" in model_string:
        framework, model_id = model_string.split(":", 1)
    else:
        # Fallback for legacy format
        framework = "litellm"
        model_id = model_string
    
    # Parse model configuration from file and overrides
    try:
        model_config_dict = parse_model_config(config_file, config_overrides)
        logger.debug(f"Parsed model config: {len(model_config_dict)} properties")
    except ModelConfigError as e:
        logger.error(f"Model configuration error: {e}")
        raise ValueError(f"Model configuration error: {e}")
    
    # Add framework and model_id to the config dict
    model_config_dict['framework'] = framework
    model_config_dict['model_id'] = model_id
    
    # Create ModelConfig with all the configuration
    model_config = ModelConfig(**model_config_dict)
    
    return model_config