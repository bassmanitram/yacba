"""
YACBA Configuration Dataclass

Central configuration dataclass for YACBA with rich annotations for automatic
CLI generation via dataclass-args.

This dataclass serves as the single source of truth for all configuration,
with annotations that drive both CLI argument generation and validation.

Field order determines --help output order: common options first, then grouped by functionality.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

from yacba_types import FileUpload, Message, PathLike

# Import dataclass-args annotations
from dataclass_args import (
    cli_help,
    cli_exclude,
    cli_short,
    cli_choices,
    cli_file_loadable,
    combine_annotations,
)

# Type alias for conversation manager
ConversationManagerType = Literal["null", "sliding_window", "summarizing"]


@dataclass
class YacbaConfig:
    """YACBA - Yet Another ChatBot Agent

    A flexible chatbot system with support for multiple AI providers,
    conversation management, and tool usage.

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

    Field order determines help output order - most common options are listed first.
    """

    # ========================================================================
    # Common Options (shown first in --help)
    # ========================================================================

    model_string: str = combine_annotations(
        cli_short("m"),
        cli_help(
            "The model to use (format: framework:model_name, e.g., 'litellm:gpt-4', 'bedrock:anthropic.claude-v2')"
        ),
        default="litellm:gemini/gemini-2.5-flash",
    )

    system_prompt: str = combine_annotations(
        cli_short("s"),
        cli_file_loadable(),
        cli_help("System prompt for the agent"),
        default=(
            "You are a highly capable AI assistant with access to various tools "
            "and the ability to read and analyze files. Provide helpful, accurate, "
            "and contextual responses."
        ),
    )

    headless: bool = combine_annotations(
        cli_short("H"),
        cli_help("Headless mode (reads from stdin, no interactive prompt)"),
        default=False,
    )

    initial_message: Optional[str] = combine_annotations(
        cli_short("i"),
        cli_file_loadable(),
        cli_help("Initial message to send to the agent"),
        default=None,
    )

    session_name: Optional[str] = cli_help(
        "Session name for conversation persistence", default=None
    )

    # ========================================================================
    # Tools Configuration (grouped together)
    # ========================================================================

    tool_configs_dir: Optional[str] = combine_annotations(
        cli_short("t"),
        cli_help("Directory containing tool configuration files"),
        default=None,
    )

    # ========================================================================
    # Model Configuration (grouped together)
    # ========================================================================

    model_config: Dict[str, Any] = cli_help(
        "Model configuration file (JSON or YAML)", default_factory=dict
    )

    emulate_system_prompt: bool = combine_annotations(
        cli_help(
            "Emulate system prompt via user message (for models without system prompt support)"
        ),
        default=False,
    )

    disable_context_repair: bool = combine_annotations(
        cli_help("Disable automatic context repair when token limits are exceeded"),
        default=False,
    )

    # ========================================================================
    # Conversation Management (grouped together)
    # ========================================================================

    conversation_manager_type: ConversationManagerType = combine_annotations(
        cli_choices(["null", "sliding_window", "summarizing"]),
        cli_help("Conversation management strategy"),
        default="sliding_window",
    )

    sliding_window_size: int = cli_help(
        "Number of messages to keep in sliding window", default=40
    )

    preserve_recent_messages: int = cli_help(
        "Number of recent messages to always preserve when summarizing", default=10
    )

    summary_ratio: float = cli_help(
        "Ratio of summary length to original (0.0-1.0) when summarizing", default=0.3
    )

    summarization_model: Optional[str] = cli_help(
        "Model to use for summarization (defaults to main model if not specified)",
        default=None,
    )

    summarization_model_config: Dict[str, Any] = cli_help(
        "Summarization model configuration file (JSON or YAML)", default_factory=dict
    )

    custom_summarization_prompt: Optional[str] = combine_annotations(
        cli_file_loadable(), cli_help("Custom prompt for summarization"), default=None
    )

    should_truncate_results: bool = cli_help(
        "Truncation of long tool results in conversation history", default=True
    )

    # ========================================================================
    # File Handling (grouped together)
    # ========================================================================

    max_files: int = cli_help("Maximum number of files to process", default=20)

    # ========================================================================
    # Session & Agent Management (grouped together)
    # ========================================================================

    agent_id: Optional[str] = cli_help("Agent ID for session management", default=None)

    # ========================================================================
    # Output & UI Customization (grouped together)
    # ========================================================================

    show_tool_use: bool = cli_help("Tool usage information display", default=False)

    cli_prompt: Optional[str] = combine_annotations(
        cli_file_loadable(), cli_help("Custom CLI prompt string"), default=None
    )

    response_prefix: Optional[str] = combine_annotations(
        cli_file_loadable(), cli_help("Custom response prefix string"), default=None
    )

    # ========================================================================
    # Internal Fields (not exposed to CLI)
    # ========================================================================

    tool_config_paths: List[PathLike] = cli_exclude(default_factory=list)
    startup_files_content: Optional[List[Message]] = cli_exclude(default=None)
    prompt_source: str = cli_exclude(default="default")
    files_to_upload: List[FileUpload] = cli_exclude(default_factory=list)
    tool_discovery_result: Optional[str] = cli_exclude(default=None)

    @property
    def has_session(self) -> bool:
        """Check if session persistence is enabled."""
        return self.session_name is not None
