"""
YACBA Configuration Dataclass

Central configuration dataclass for YACBA using cli_nested to compose
AgentFactoryConfig directly, eliminating the need for a converter.

This uses dataclass-args cli_nested feature to flatten both AgentFactoryConfig
and YACBA-specific config into a single CLI surface.
"""

from dataclasses import dataclass
from typing import List, Optional

from strands_agent_factory import AgentFactoryConfig
from yacba_types import FileUpload, Message

# Import dataclass-args annotations
from dataclass_args import (
    cli_help,
    cli_exclude,
    cli_short,
    cli_file_loadable,
    cli_nested,
    combine_annotations,
)


@dataclass
class YacbaREPLConfig:
    """YACBA-specific REPL and UI configuration.
    
    These are the only fields that are truly YACBA-specific and not part of
    the AgentFactoryConfig from strands-agent-factory.
    """

    headless: bool = combine_annotations(
        cli_short("H"),
        cli_help("Headless mode (reads from stdin, no interactive prompt)"),
        default=False,
    )

    cli_prompt: Optional[str] = combine_annotations(
        cli_file_loadable(),
        cli_help("Custom CLI prompt string"),
        default=None,
    )

    max_files: int = cli_help(
        "Maximum number of files to process",
        default=20,
    )


@dataclass
class YacbaConfig:
    """YACBA - Yet Another ChatBot Agent

    Top-level configuration that composes AgentFactoryConfig (from strands-agent-factory)
    with YACBA-specific REPL configuration.
    
    Both are flattened (prefix="") into the CLI, providing a clean command-line interface
    with no duplication between YACBA and strands-agent-factory fields.
    
    Structure:
    - agent: AgentFactoryConfig (all agent/model/conversation config)
    - repl: YacbaREPLConfig (YACBA-specific UI config)
    - Internal fields (populated by config factory at runtime)
    
    The agent field can be passed directly to AgentFactory with no conversion needed!
    """

    # Nest AgentFactoryConfig with NO prefix (complete flattening)
    # This gives us -m, -s, -i, -f, -t and all other AgentFactoryConfig CLI args
    agent: AgentFactoryConfig = cli_nested(prefix="")

    # Nest YacbaREPLConfig with NO prefix (complete flattening)
    # No field name conflicts, so we get clean --headless, --cli-prompt, --max-files
    repl: YacbaREPLConfig = cli_nested(prefix="")

    # ========================================================================
    # Internal Fields (not exposed to CLI)
    # ========================================================================
    # These are populated by the config factory or at runtime

    startup_files_content: Optional[List[Message]] = cli_exclude(default=None)
    """Content of startup files to send to agent (populated by config factory)"""

    files_to_upload: List[FileUpload] = cli_exclude(default_factory=list)
    """Processed file uploads (populated from agent.file_paths by config factory)"""

    prompt_source: str = cli_exclude(default="default")
    """Tracking where the system prompt came from (CLI, config, or default)"""

    tool_discovery_result: Optional[str] = cli_exclude(default=None)
    """Result message from tool discovery process"""

    # ========================================================================
    # Utility Properties
    # ========================================================================

    @property
    def has_session(self) -> bool:
        """Check if session persistence is enabled."""
        return self.agent.session_id is not None
