"""
Typed configuration object for YACBA focused on core responsibilities.

YACBA manages:
- Model configuration and framework selection
- Tool configuration (not execution)
- File processing and session persistence
- CLI orchestration

Tool execution and protocol details are handled by strands-agents.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Literal
from pathlib import Path

# Import our focused types
from yacba_types.config import ModelConfig, ToolConfig, FileUpload, ToolDiscoveryResult
from yacba_types.content import Message

# Type for conversation manager strategies
ConversationManagerType = Literal["null", "sliding_window", "summarizing"]

@dataclass
class YacbaConfig:
    """
    A strongly typed data class for YACBA's core configuration responsibilities.
    Focused on what YACBA manages, not what strands-agents handles.
    """
    # Core configuration (YACBA's primary responsibilities)
    model_string: str                           # Model selection and framework detection
    system_prompt: str                          # System prompt management
    prompt_source: str                          # Source tracking for debugging
    tool_configs: List[ToolConfig]              # Tool configuration (not execution)
    startup_files_content: Optional[List[Message]]  # Processed startup files
    
    # Optional configuration with defaults
    headless: bool = False                      # CLI mode selection
    model_config: ModelConfig = field(default_factory=dict)  # Model parameters
    session_name: Optional[str] = None          # Session persistence
    agent_id: Optional[str] = None              # Session namespace
    emulate_system_prompt: bool = False         # Framework compatibility
    show_tool_use: bool = False
    
    initial_message: Optional[str] = None       # Initial user input
    max_files: int = 20                         # File processing limits
    files_to_upload: List[FileUpload] = field(default_factory=list)  # File queue
    
    # Tool discovery results for startup reporting
    tool_discovery_result: Optional['ToolDiscoveryResult'] = None
    
    # Conversation Manager Configuration
    conversation_manager_type: ConversationManagerType = "sliding_window"  # Default to sliding window
    sliding_window_size: int = 40               # Maximum messages in sliding window
    preserve_recent_messages: int = 10          # Messages to always preserve in summarizing mode
    summary_ratio: float = 0.3                  # Ratio of messages to summarize (0.1-0.8)
    summarization_model: Optional[str] = None   # Optional separate model for summarization
    custom_summarization_prompt: Optional[str] = None  # Custom prompt for summarization
    should_truncate_results: bool = True        # Whether to truncate tool results on overflow
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate_model_string()
        self._validate_max_files()
        self._validate_files_to_upload()
        self._validate_conversation_manager_config()
    
    def _validate_model_string(self) -> None:
        """Validate the model string format for framework detection."""
        if not self.model_string:
            raise ValueError("model_string cannot be empty")
        
        # Basic format validation for framework:model pattern
        if ":" in self.model_string:
            framework, model = self.model_string.split(":", 1)
            if not framework or not model:
                raise ValueError(f"Invalid model string format: {self.model_string}")
    
    def _validate_max_files(self) -> None:
        """Validate max_files is reasonable for file processing."""
        if self.max_files < 1:
            raise ValueError("max_files must be at least 1")
        if self.max_files > 1000:
            raise ValueError("max_files cannot exceed 1000 (performance limit)")
    
    def _validate_files_to_upload(self) -> None:
        """Validate files to upload exist and are accessible."""
        for file_info in self.files_to_upload:
            path = Path(file_info["path"])
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            if not path.is_file():
                raise ValueError(f"Path is not a file: {path}")
    
    def _validate_conversation_manager_config(self) -> None:
        """Validate conversation manager configuration parameters."""
        # Validate sliding window size
        if self.sliding_window_size < 1:
            raise ValueError("sliding_window_size must be at least 1")
        if self.sliding_window_size > 1000:
            raise ValueError("sliding_window_size cannot exceed 1000 (performance limit)")
        
        # Validate preserve_recent_messages
        if self.preserve_recent_messages < 1:
            raise ValueError("preserve_recent_messages must be at least 1")
        
        # Only validate preserve_recent against sliding_window for summarizing mode
        if self.conversation_manager_type == "summarizing":
            # For summarizing mode, preserve_recent should be reasonable but not tied to sliding_window
            if self.preserve_recent_messages > 100:
                raise ValueError("preserve_recent_messages cannot exceed 100 (performance limit)")
        
        # Validate summary_ratio
        if not (0.1 <= self.summary_ratio <= 0.8):
            raise ValueError("summary_ratio must be between 0.1 and 0.8")
        
        # Validate summarization model format if provided
        if self.summarization_model:
            if ":" in self.summarization_model:
                framework, model = self.summarization_model.split(":", 1)
                if not framework or not model:
                    raise ValueError(f"Invalid summarization_model format: {self.summarization_model}")
    
    @property
    def has_startup_files(self) -> bool:
        """Check if there are startup files configured."""
        return bool(self.files_to_upload)
    
    @property
    def framework_name(self) -> str:
        """Extract framework name from model string for loader selection."""
        if ":" in self.model_string:
            return self.model_string.split(":", 1)[0]
        return "litellm"  # Default framework
    
    @property
    def model_name(self) -> str:
        """Extract model name from model string for framework configuration."""
        if ":" in self.model_string:
            return self.model_string.split(":", 1)[1]
        return self.model_string
    
    @property
    def is_interactive(self) -> bool:
        """Check if running in interactive mode."""
        return not self.headless
    
    @property
    def has_session(self) -> bool:
        """Check if session persistence is enabled."""
        return self.session_name is not None
    
    @property
    def uses_conversation_manager(self) -> bool:
        """Check if conversation management is enabled."""
        return self.conversation_manager_type != "null"
    
    @property
    def uses_sliding_window(self) -> bool:
        """Check if using sliding window conversation management."""
        return self.conversation_manager_type == "sliding_window"
    
    @property
    def uses_summarizing(self) -> bool:
        """Check if using summarizing conversation management."""
        return self.conversation_manager_type == "summarizing"

    # Performance optimization settings
    clear_cache: bool = False
    show_perf_stats: bool = False
    disable_cache: bool = False