# yacba_config.py
# Defines a typed configuration object for the YACBA application.

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class YacbaConfig:
    """
    A typed data class to hold all configuration for the YACBA application,
    decoupling the core logic from the command-line parser.
    """
    model_string: str
    system_prompt: str
    prompt_source: str
    tool_configs: List[Dict[str, Any]]
    startup_files_content: Optional[List[Dict[str, Any]]]
    
    headless: bool = False
    model_config: Dict[str, Any] = field(default_factory=dict)
    session_name: Optional[str] = None
    emulate_system_prompt: bool = False
    
    # CLI-specific fields that are not part of the core engine config
    initial_message: Optional[str] = None
    max_files: int = 20
    files_to_upload: List[tuple[str, str]] = field(default_factory=list)
