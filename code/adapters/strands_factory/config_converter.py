"""
Configuration converter from YACBA to strands_agent_factory.

This module handles the translation of YACBA's sophisticated configuration
system into the simpler AgentFactoryConfig format required by strands_agent_factory.
"""

from pathlib import Path
from typing import List, Tuple, Optional, Any, Dict, Literal

from utils.logging import get_logger

from strands_agent_factory import AgentFactoryConfig
from config.dataclass import YacbaConfig

logger = get_logger(__name__)

# Import create_auto_printer - available in project virtual environment
try:
    from repl_toolkit import create_auto_printer
except ImportError:
    # Fallback for testing outside project venv
    create_auto_printer = lambda: print

# Define the type locally since it's just a literal
ConversationManagerType = Literal["null", "sliding_window", "summarizing"]


class YacbaToStrandsConfigConverter:
    """
    Converts YACBA configuration to strands_agent_factory configuration.
    
    This converter handles the mapping between YACBA's comprehensive configuration
    system and the streamlined AgentFactoryConfig used by strands_agent_factory.
    """
    
    def __init__(self, yacba_config: YacbaConfig):
        """
        Initialize the converter with YACBA configuration.
        
        Args:
            yacba_config: The parsed YACBA configuration object
        """
        self.yacba_config = yacba_config
        logger.debug("config_converter_initialized", model=yacba_config.model_string)
    
    def convert(self) -> AgentFactoryConfig:
        """
        Convert YACBA configuration to AgentFactoryConfig.
        
        Returns:
            AgentFactoryConfig: Converted configuration for strands_agent_factory
        """
        logger.debug("converting_yacba_config_to_strands_config")
        
        # Convert tool configurations to paths
        tool_config_paths = self._convert_tool_configs()
        
        # Convert file uploads to file paths
        file_paths = self._convert_file_uploads()
        
        # Determine session configuration
        sessions_home = self._get_sessions_home()
        
        # Create the AgentFactoryConfig
        config = AgentFactoryConfig(
            # Core model configuration
            model=self.yacba_config.model_string,
            system_prompt=self.yacba_config.system_prompt,
            model_config=self.yacba_config.model_config,
            emulate_system_prompt=self.yacba_config.emulate_system_prompt,
            # NOTE: disable_context_repair parameter will be added when strands_agent_factory is updated
            # disable_context_repair=self.yacba_config.disable_context_repair,
            
            # Initial message and files
            initial_message=self._build_initial_message(),
            file_paths=file_paths,
            
            # Tool configuration
            tool_config_paths=tool_config_paths,
            
            # Session management
            session_id=self.yacba_config.session_name,
            sessions_home=sessions_home,
            
            # Conversation management
            conversation_manager_type=self._convert_conversation_manager_type(),
            sliding_window_size=self.yacba_config.sliding_window_size,
            preserve_recent_messages=self.yacba_config.preserve_recent_messages,
            summary_ratio=self.yacba_config.summary_ratio,
            summarization_model=self.yacba_config.summarization_model,
            summarization_model_config=self.yacba_config.summarization_model_config,
            custom_summarization_prompt=self.yacba_config.custom_summarization_prompt,
            should_truncate_results=self.yacba_config.should_truncate_results,
            
            # UI customization
            show_tool_use=self.yacba_config.show_tool_use,
            response_prefix=self.yacba_config.response_prefix,
            output_printer=create_auto_printer() if not self.yacba_config.headless else print,  # Auto-format HTML/ANSI in interactive mode
        )
        
        logger.debug("config_conversion_complete", 
                    tool_configs=len(tool_config_paths), 
                    files=len(file_paths))
        return config
    
    def _convert_tool_configs(self) -> List[Path]:
        """
        Convert YACBA tool configuration paths to Path objects.
        
        Returns:
            List[Path]: List of paths to tool configuration files/directories
        """
        if not self.yacba_config.tool_config_paths:
            return []
        
        # Convert path-like objects to Path objects
        result = []
        for path_like in self.yacba_config.tool_config_paths:
            result.append(Path(path_like))
        
        logger.debug("tool_config_paths_converted", count=len(self.yacba_config.tool_config_paths))
        return result
    
    def _convert_file_uploads(self) -> List[Tuple[Path, Optional[str]]]:
        """
        Convert YACBA file uploads to strands_agent_factory file paths format.
        
        Returns:
            List[Tuple[Path, Optional[str]]]: List of (path, mimetype) tuples
        """
        if not self.yacba_config.files_to_upload:
            return []
        
        result = []
        for file_upload in self.yacba_config.files_to_upload:
            # Handle different file upload formats
            if isinstance(file_upload, dict):
                path = Path(file_upload['path'])
                mimetype = file_upload.get('mimetype')
            elif isinstance(file_upload, (list, tuple)) and len(file_upload) >= 2:
                path = Path(file_upload[0])
                mimetype = file_upload[1] if len(file_upload) > 1 else None
            else:
                # Assume it's just a path
                path = Path(file_upload)
                mimetype = None
            
            result.append((path, mimetype))
        
        logger.debug("file_uploads_converted", count=len(self.yacba_config.files_to_upload))
        return result
    
    def _get_sessions_home(self) -> Optional[Path]:
        """
        Determine the sessions home directory.
        
        Returns:
            Optional[Path]: Sessions directory path if session persistence is enabled
        """
        if not self.yacba_config.has_session:
            return None
        
        # Use a default sessions directory - could be made configurable
        return Path.home() / ".yacba" / "sessions"
    
    def _build_initial_message(self) -> Optional[str]:
        """
        Build the initial message from YACBA configuration.
        
        Returns:
            Optional[str]: Initial message text, or None if no initial message
        """
        # YACBA handles file content separately via startup_files_content
        # The initial_message should just be the user's explicit initial message
        return self.yacba_config.initial_message
    
    def _convert_conversation_manager_type(self) -> ConversationManagerType:
        """
        Convert YACBA conversation manager type to strands_agent_factory type.
        
        Returns:
            ConversationManagerType: Converted conversation manager type
        """
        # The types should match, but we'll be explicit about the conversion
        yacba_type = self.yacba_config.conversation_manager_type
        
        if yacba_type == "null":
            return "null"
        elif yacba_type == "sliding_window":
            return "sliding_window"
        elif yacba_type == "summarizing":
            return "summarizing"
        else:
            logger.warning("unknown_conversation_manager_type", 
                          type=yacba_type, 
                          default="sliding_window")
            return "sliding_window"
