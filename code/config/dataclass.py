"""
YACBA Configuration Dataclass

Central configuration dataclass for YACBA with rich annotations for automatic
CLI generation via dataclass-args.

This dataclass serves as the single source of truth for all configuration,
with annotations that drive both CLI argument generation and validation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from yacba_types import FileUpload, Message, PathLike

# Import dataclass-args annotations
from dataclass_args import cli_help, cli_exclude, cli_short, cli_choices, cli_file_loadable, combine_annotations

# Type alias for conversation manager
ConversationManagerType = Literal['null', 'sliding_window', 'summarizing']


@dataclass
class YacbaConfig:
    """
    Configuration for YACBA with rich annotations for CLI generation.
    
    Fields are annotated with dataclass-args annotations to automatically generate:
    - CLI arguments (--model-string, --system-prompt, etc.)
    - Short aliases (-m, -s, -i, -H)
    - Help text
    - Type handling (str, int, bool, dict, Path, Optional, etc.)
    - File loading (@file.txt syntax)
    - Validation (choices for enums)
    - Boolean flags (--flag / --no-flag)
    - Dict overrides (--mc key:value)
    
    Fields marked with cli_exclude() are not exposed to CLI - they're internal fields
    populated by configuration factory or runtime logic.
    """
    
    # ========================================================================
    # Core Configuration
    # ========================================================================
    
    model_string: str = combine_annotations(
        cli_short('m'),
        cli_help("The model to use (format: framework:model_name, e.g., 'litellm:gpt-4', 'bedrock:anthropic.claude-v2')"),
        default="litellm:gemini/gemini-2.5-flash"
    )
    
    # Internal fields - not exposed to CLI
    tool_config_paths: List[PathLike] = cli_exclude(default_factory=list)
    startup_files_content: Optional[List[Message]] = cli_exclude(default=None)
    prompt_source: str = cli_exclude(default="default")
    
    # ========================================================================
    # System Prompt
    # ========================================================================
    
    system_prompt: str = combine_annotations(
        cli_short('s'),
        cli_file_loadable(),
        cli_help("System prompt for the agent. Use @file.txt to load from file"),
        default=(
            "You are a highly capable AI assistant with access to various tools "
            "and the ability to read and analyze files. Provide helpful, accurate, "
            "and contextual responses."
        )
    )
    
    emulate_system_prompt: bool = combine_annotations(
        cli_help("Emulate system prompt via user message (for models without system prompt support)"),
        default=False
    )
    
    # ========================================================================
    # Model Configuration
    # ========================================================================
    
    model_config: Dict[str, Any] = cli_help(
        "Model configuration parameters (JSON file or use --mc for property overrides)",
        default_factory=dict
    )
    
    summarization_model_config: Dict[str, Any] = cli_help(
        "Summarization model configuration parameters when using '--conversation_manager_type summarizing' (JSON file or use --smc for property overrides)",
        default_factory=dict
    )
    
    # ========================================================================
    # File Handling
    # ========================================================================
    
    files_to_upload: List[FileUpload] = cli_exclude(default_factory=list)  # Complex handling via FilesSpec
    
    max_files: int = cli_help("Maximum number of files to process", default=20)
    
    tool_configs_dir: Optional[str] = cli_exclude(default=None)  # Manually handled with -t
    
    tool_discovery_result: Optional[str] = cli_exclude(default=None)
    
    # ========================================================================
    # Session Management
    # ========================================================================
    
    session_name: Optional[str] = cli_help(
        "Session name for conversation persistence",
        default=None
    )
    
    agent_id: Optional[str] = cli_help(
        "Agent ID for session management",
        default=None
    )
    
    @property
    def has_session(self) -> bool:
        """Check if session persistence is enabled."""
        return self.session_name is not None
    
    # ========================================================================
    # Conversation Management
    # ========================================================================
    
    conversation_manager_type: ConversationManagerType = combine_annotations(
        cli_choices(['null', 'sliding_window', 'summarizing']),
        cli_help("Conversation management strategy: null (no management), sliding_window (keep recent), summarizing (with summaries)"),
        default="sliding_window"
    )
    
    # Sliding Window settings
    sliding_window_size: int = cli_help(
        "Number of messages to keep in sliding window",
        default=40
    )
    
    preserve_recent_messages: int = cli_help(
        "Number of recent messages to always preserve when summarizing",
        default=10
    )
    
    # Summarization settings
    summary_ratio: float = cli_help(
        "Ratio of summary length to original (0.0-1.0) when summarizing",
        default=0.3
    )
    
    summarization_model: Optional[str] = cli_help(
        "Model to use in the summarization Agent when summarizing (defaults to main model if not specified)",
        default=None
    )
    
    custom_summarization_prompt: Optional[str] = combine_annotations(
        cli_file_loadable(),
        cli_help("Custom prompt for summarization. Use @file.txt to load from file"),
        default=None
    )
    
    should_truncate_results: bool = cli_help(
        "Truncate long tool results in conversation history",
        default=True
    )
    
    # ========================================================================
    # Execution Mode
    # ========================================================================
    
    headless: bool = combine_annotations(
        cli_short('H'),
        cli_help("Run in headless mode (reads from stdin, no interactive prompt)"),
        default=False
    )
    
    initial_message: Optional[str] = combine_annotations(
        cli_short('i'),
        cli_file_loadable(),
        cli_help("Initial message to send to the agent. Use @file.txt to load from file"),
        default=None
    )
    
    # ========================================================================
    # Output Control
    # ========================================================================
    
    show_tool_use: bool = cli_help(
        "Display tool usage information",
        default=False
    )
    
    # ========================================================================
    # User Interface Customization
    # ========================================================================
    
    cli_prompt: Optional[str] = combine_annotations(
        cli_file_loadable(),
        cli_help("Custom CLI prompt string. Use @file.txt to load from file"),
        default=None
    )
    
    response_prefix: Optional[str] = combine_annotations(
        cli_file_loadable(),
        cli_help("Custom response prefix string. Use @file.txt to load from file"),
        default=None
    )
