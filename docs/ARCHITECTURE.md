# YACBA Architecture Documentation

## Overview

YACBA is a **CLI wrapper** built on top of [strands-agent-factory](https://github.com/bassmanitram/strands-agent-factory), which itself is built on [strands-agents](https://github.com/pydantic/strands-agents).

**YACBA's Role**: Provide command-line interface, configuration management, profile system, and interactive REPL on top of strands-agent-factory's core agent functionality.

**Core Functionality** (LLM integration, tool execution, conversation management, A2A support) comes from strands-agent-factory.

> **Note**: This documents YACBA's wrapper architecture only. For core agent architecture,  
> see [strands-agent-factory documentation](https://github.com/bassmanitram/strands-agent-factory).

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Component Diagrams](#component-diagrams)
3. [Data Flow](#data-flow)
4. [Design Patterns](#design-patterns)
5. [Module Structure](#module-structure)
6. [Configuration System](#configuration-system)
7. [Adapter Pattern Implementation](#adapter-pattern-implementation)
8. [Extension Points](#extension-points)
9. [Testing Strategy](#testing-strategy)
10. [Performance Considerations](#performance-considerations)

---

## High-Level Architecture

### System Layering

YACBA sits atop strands-agent-factory as a thin wrapper:

```
┌──────────────────────────────────────────────────────┐
│                  strands-agents                      │
│            (Core AI Agent Framework)                 │
│                                                      │
│  • LLM abstractions    • Message handling            │
│  • Tool protocols      • Streaming responses         │
└────────────────────┬─────────────────────────────────┘
                     │
                     │ builds on
                     ▼
┌──────────────────────────────────────────────────────┐
│            strands-agent-factory                     │
│         (Agent Lifecycle & Management)               │
│                                                      │
│  • AgentFactory        • Tool loading (Py/MCP/A2A)   │
│  • AgentProxy          • Conversation management     │
│  • Provider adapters   • Session persistence         │
│  • Tool types          • File handling               │
└────────────────────┬─────────────────────────────────┘
                     │
                     │ wrapped by
                     ▼
┌──────────────────────────────────────────────────────┐
│                    YACBA                             │
│              (CLI Wrapper Layer)                     │
│                                                      │
│  • CLI parsing (dataclass-args)                      │
│  • Profile system (profile-config)                   │
│  • Interactive REPL (repl-toolkit)                   │
│  • Configuration conversion                          │
│  • File glob processing                              │
│  • Headless mode                                     │
│  • Session repair utilities                          │
└──────────────────────────────────────────────────────┘
```

### What Each Layer Provides

**strands-agents** (Foundation):
- LLM provider abstractions
- Tool execution protocols
- Message streaming
- Response handling

**strands-agent-factory** (Core Functionality):
- Agent creation and lifecycle
- Tool loading (Python functions, MCP servers, A2A)
- Conversation management strategies
- Session persistence
- Provider configuration

**YACBA** (Wrapper Layer):
- Command-line interface with meta-arguments
- Configuration profiles (profile-config)
- Interactive REPL with completion
- Headless automation mode
- Configuration file discovery
- Glob pattern file loading
- Session repair tools

---

## Component Diagrams

### Package Structure

```
yacba/
├── code/
│   ├── yacba.py                    # Main entry point, orchestration
│   ├── config/                     # Configuration system
│   │   ├── __init__.py             # Exports parse_config, YacbaConfig
│   │   ├── arguments.py            # Default values, env var mappings
│   │   ├── dataclass.py            # YacbaConfig dataclass (CLI source)
│   │   └── factory.py              # Configuration parsing/merging
│   ├── adapters/                   # Adapter implementations
│   │   ├── strands_factory/        # strands-agent-factory adapters
│   │   │   ├── __init__.py
│   │   │   └── config_converter.py # YACBA config → strands config
│   │   └── repl_toolkit/           # repl-toolkit adapters
│   │       ├── __init__.py
│   │       ├── backend.py          # Backend protocol implementation
│   │       ├── completer.py        # File path completion
│   │       └── actions/            # Interactive commands
│   │           ├── __init__.py
│   │           ├── registry.py     # Command registry
│   │           ├── status_action.py
│   │           ├── session_actions.py
│   │           └── info_actions.py
│   ├── utils/                      # Utility modules
│   │   ├── __init__.py
│   │   ├── file_utils.py           # File/tool config discovery
│   │   ├── config_utils.py         # Config file loading
│   │   ├── model_config_parser.py  # Model config parsing
│   │   ├── general_utils.py        # General utility functions
│   │   ├── startup_messages.py     # Welcome/info display
│   │   └── logging.py              # Centralized logging (envlog)
│   ├── scripts/                    # Maintenance utilities
│   │   └── fix_strands_session.py  # Session repair tool
│   ├── yacba_types/                # Type definitions
│   │   ├── __init__.py
│   │   ├── base.py                 # Exit codes
│   │   ├── config.py               # Config types
│   │   └── content.py              # Content types
│   └── tests/                      # Test suite
│       ├── __init__.py
│       ├── conftest.py             # Pytest configuration
│       ├── config/                 # Config tests
│       └── unit/                   # Unit tests
│           ├── test_factory.py
│           ├── test_arguments.py
│           ├── test_completer.py
│           ├── test_model_config_parser.py
│           ├── test_config_utils.py
│           ├── test_general_utils.py
│           ├── test_file_utils.py
│           ├── test_config_converter.py
│           └── test_yacba_types.py
├── sample-tool-configs/            # Example tool configurations
│   ├── strands.tools.json          # Python function tools
│   ├── aws-cli.tools.json          # MCP server (AWS CLI)
│   ├── aws-doc.tools.json          # MCP server (AWS docs)
│   ├── local-files.tools.json      # MCP server (local files)
│   └── a2a-example.tools.json      # A2A (Agent-to-Agent) tools
├── sample-model-configs/           # Example model configurations
│   ├── openai-gpt4.json
│   ├── anthropic-claude.json
│   ├── bedrock-claude.json
│   └── litellm-gemini.json
├── sample-python-tools/            # Example Python function tools
│   └── local_tools.py
├── docs/                           # Documentation
│   ├── README.md
│   ├── ARCHITECTURE.md             # This file
│   ├── API.md
│   ├── TROUBLESHOOTING.md
│   └── COMPLETION_SYSTEM.md
├── .strands-sessions/              # Session persistence (runtime)
├── README.md                       # Main documentation
└── requirements.txt                # Python dependencies
```

### Component Interaction Flow

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │ CLI args
       ▼
┌─────────────────┐
│  yacba.py       │
│  (Main)         │
└──────┬──────────┘
       │ parse_config()
       ▼
┌─────────────────┐
│  config/        │
│  factory.py     │
│  (profile-      │
│   config)       │
└──────┬──────────┘
       │ YacbaConfig
       ▼
┌─────────────────────────┐
│  YacbaToStrands         │
│  ConfigConverter        │
└──────┬──────────────────┘
       │ AgentFactoryConfig
       ▼
┌─────────────────────────┐
│  strands_agent_factory  │
│  AgentFactory           │
└──────┬──────────────────┘
       │ AgentProxy
       ▼
┌─────────────────────────┐
│  YacbaBackend           │
│  (adapter)              │
└──────┬──────────────────┘
       │ Backend protocol
       ▼
┌─────────────────────────┐
│  repl_toolkit           │
│  AsyncREPL/HeadlessREPL │
└──────┬──────────────────┘
       │ user interaction
       ▼
┌─────────────┐
│   User      │
└─────────────┘
```

---

## Data Flow

### Configuration Flow

Configuration precedence using **profile-config** and **dataclass-args**:

```
┌─────────────────┐
│  ARGUMENT       │  ← Fallback values (arguments.py)
│  DEFAULTS       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Profile File   │  ← ~/.yacba/config.yaml or ./.yacba/config.yaml
│  (profile-      │     (resolved via profile-config)
│   config)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Environment    │  ← YACBA_* environment variables
│  Variables      │     (YACBA_MODEL_STRING, YACBA_PROFILE, etc.)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  --config       │  ← Explicit config file from CLI
│  (base_configs) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  CLI Arguments  │  ← Highest priority
│  (dataclass-    │     (-m, -s, --model-string, etc.)
│   args)         │
└─────────────────┘
```

**Implementation Details**:
1. **profile-config** resolves: DEFAULTS → PROFILE → ENV VARS
2. **@file.txt processing**: Manual processing for profile/env values (dataclass-args only processes CLI)
3. **dataclass-args** applies: profile_config → --config → CLI args (via `base_configs` parameter)
4. **YACBA post-processing**: Tool discovery, prompt source detection

**Meta-Arguments** (handled separately, not in YacbaConfig):
- `--profile <name>` - Select configuration profile
- `--list-profiles` - List available profiles
- `--show-config` - Display resolved configuration
- `--init-config <path>` - Create sample configuration file
- `YACBA_PROFILE` - Environment variable for profile selection

### Message Flow (Interactive Mode)

```
User Input
    │
    ▼
┌─────────────────────┐
│  AsyncREPL          │  (repl-toolkit)
│  • Input capture    │
│  • Tab completion   │
│  • History          │
│  • Ctrl+C cancel    │
└──────────┬──────────┘
           │
           ▼ /command or message?
           │
    ┌──────┴──────┐
    │             │
    ▼ command     ▼ message
┌─────────┐   ┌──────────────┐
│ Action  │   │ YacbaBackend │
│ Handler │   └──────┬───────┘
│ (/tools,│          │
│ /status,│          ▼
│ /save)  │   ┌──────────────────┐
└─────────┘   │  AgentProxy      │  (strands-agent-factory)
              │  (context mgr)   │
              │  • send_message  │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  strands-agents  │
              │  • LLM calls     │
              │  • Tool exec     │
              │  • Streaming     │
              └────────┬─────────┘
                       │
                       ▼ response stream
              ┌──────────────────┐
              │  YacbaBackend    │
              │  (async iterator)│
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  AsyncREPL       │
              │  (display with   │
              │   auto-format)   │
              └────────┬─────────┘
                       │
                       ▼
               User sees output
```

### Message Flow (Headless Mode)

```
stdin or -i
    │
    ▼
┌─────────────────────┐
│  HeadlessREPL       │  (repl-toolkit)
│  • Read stdin       │
│  • /send separator  │
│  • EOF detection    │
└──────────┬──────────┘
           │
           ▼ /command or message?
           │
    ┌──────┴──────┐
    │             │
    ▼ command     ▼ message
┌─────────┐   ┌──────────────┐
│ Action  │   │ YacbaBackend │
│ Handler │   └──────┬───────┘
└─────────┘          │
                     ▼
           ┌──────────────────┐
           │  AgentProxy      │
           │  • send_message  │
           └────────┬─────────┘
                    │
                    ▼
           ┌──────────────────┐
           │  strands-agents  │
           └────────┬─────────┘
                    │
                    ▼ response stream
           ┌──────────────────┐
           │  YacbaBackend    │
           └────────┬─────────┘
                    │
                    ▼
           ┌──────────────────┐
           │  HeadlessREPL    │
           │  (print to       │
           │   stdout)        │
           └────────┬─────────┘
                    │
                    ▼
                stdout output
```

**Headless Mode Specifics**:
- **Input**: Reads from stdin until EOF or `/send` separator
- **Output**: Direct to stdout (no formatting)
- **Printer**: Uses plain `print()` instead of `create_auto_printer()`
- **EOF**: Ctrl+D sends accumulated input as single message
- **Multi-message**: Use `/send` to separate multiple messages in stream

---

## Design Patterns

### 1. Adapter Pattern

YACBA uses adapters to bridge between different abstractions:

**YacbaToStrandsConfigConverter**:
- Converts YacbaConfig (YACBA's format) → AgentFactoryConfig (strands format)
- Handles field name mapping, type conversion, defaults
- Maps tool_configs_dir → tool_config_paths
- Maps files_to_upload → file_paths with mimetype tuples
- Determines sessions_home based on session_name
- Creates printer abstraction (create_auto_printer vs print)

**YacbaBackend**:
- Implements repl_toolkit's Backend protocol
- Delegates to strands-agent-factory AgentProxy
- Converts between repl_toolkit events and strands response streams
- Handles async iteration of responses
- Manages agent context (with agent as agent_context)

**YacbaActionRegistry**:
- Implements repl_toolkit's ActionRegistry
- Provides YACBA-specific commands (/status, /tools, /save, /load, etc.)

### 2. Protocol-Based Design

Uses protocols (interfaces) for loose coupling:

```python
# repl_toolkit defines protocols
class Backend(Protocol):
    async def send_message(self, message: str) -> AsyncIterator[Dict]: ...
    async def cancel(self): ...

# YACBA implements protocol
class YacbaBackend(Backend):
    def __init__(self, agent: AgentProxy, config: AgentFactoryConfig):
        self.agent = agent  # strands-agent-factory agent
        ...
```

Benefits:
- YACBA doesn't depend on repl_toolkit internals
- strands-agent-factory doesn't know about YACBA
- Easy to test with mock implementations

### 3. Dependency Injection

Configuration and dependencies injected at runtime:

```python
# yacba.py
config = parse_config()  # YacbaConfig (via profile-config + dataclass-args)

converter = YacbaToStrandsConfigConverter(config)
strands_config = converter.convert()  # AgentFactoryConfig

factory = AgentFactory(config=strands_config)  # Inject config
await factory.initialize()
agent = factory.create_agent()

backend = YacbaBackend(agent, strands_config)  # Inject agent + config
repl = AsyncREPL(backend=backend, ...)  # Inject backend
```

### 4. Strategy Pattern

Conversation management uses strategy pattern (in strands-agent-factory):

```python
# User selects strategy via YACBA config
config.conversation_manager_type = "sliding_window"  # or "summarizing", "null"

# Passed through converter to strands-agent-factory
strands_config.conversation_manager_type = config.conversation_manager_type

# strands-agent-factory applies strategy internally
# YACBA just passes the configuration through
```

### 5. Context Manager Pattern

Agent lifecycle managed via context manager:

```python
with agent as agent_context:
    backend = YacbaBackend(agent_context, strands_config)
    await repl.run(backend=backend, ...)
# Agent cleanup happens automatically on exit
```

### 6. Factory Pattern

Agent creation abstracted through factory:

```python
factory = AgentFactory(config=strands_config)
await factory.initialize()  # Async initialization
agent = factory.create_agent()  # Synchronous after init
```

### 7. Registry Pattern

Commands registered for dynamic lookup:

```python
class YacbaActionRegistry:
    def __init__(self, printer):
        self.actions = {}
        self.register(StatusAction(printer))
        self.register(SaveSessionAction(printer))
        # ... etc
    
    def register(self, action):
        self.actions[action.name] = action
```

### 8. Printer Abstraction Pattern

Output handling abstracted for different modes:

```python
# Interactive: HTML/ANSI formatting via print_formatted_text
# Response prefix is pre-formatted with auto_format() to prevent XML parsing issues
response_prefix = auto_format(response_prefix_string)
output_printer = print_formatted_text

# Headless: Plain text
output_printer = print
```

**Note**: The response_prefix is pre-formatted using `auto_format()` before being passed to AgentFactory. This prevents XML parsing crashes that occurred when dynamic formatting was attempted later in the pipeline.

---

## Module Structure

### Core Entry Point

**yacba.py** - Main orchestration:
```python
def main():
    config = parse_config()  # Parse CLI + profiles + env
    asyncio.run(_run_agent_lifecycle(config))

async def _run_agent_lifecycle(config):
    # 1. Convert config
    strands_config = YacbaToStrandsConfigConverter(config).convert()
    
    # 2. Create agent (via strands-agent-factory)
    factory = AgentFactory(config=strands_config)
    await factory.initialize()
    agent = factory.create_agent()
    
    # 3. Create action registry with printer
    printer = _create_stdout_printer() if config.headless else print
    action_registry = YacbaActionRegistry(printer=printer)
    
    # 4. Run appropriate mode
    if config.headless:
        await _run_headless_mode(agent, action_registry, config, strands_config)
    else:
        await _run_interactive_mode(agent, action_registry, config, strands_config)
```

**Interactive Mode Details**:
- Creates AsyncREPL with completers (commands, shell, files)
- Determines history path (session-based or default)
- Prints welcome message and startup info
- Uses agent context manager
- Auto-formatting printer (create_auto_printer)

**Headless Mode Details**:
- Creates HeadlessREPL (no completion, no history)
- Uses plain stdout printer
- Reads stdin until EOF or /send
- Uses agent context manager

### Configuration Module

**config/** - Configuration management:
- **dataclass.py**: YacbaConfig dataclass (source of truth for all CLI args)
  - Fields annotated with dataclass-args annotations
  - CLI arguments auto-generated from annotations
  - Field order determines --help output order
- **arguments.py**: ARGUMENT_DEFAULTS and ARGUMENTS_FROM_ENV_VARS
  - Fallback values for all fields
  - Environment variable integration (YACBA_* prefix)
- **factory.py**: parse_config() - Complex precedence orchestration
  - profile-config resolution (DEFAULTS → PROFILE → ENV)
  - Manual @file.txt processing for profile/env values
  - dataclass-args with base_configs (adds --config and CLI)
  - Meta-argument handling (--profile, --list-profiles, etc.)
  - YACBA post-processing (tool discovery, prompt source)
- **__init__.py**: Exports parse_config, YacbaConfig

### Adapters Module

**adapters/strands_factory/** - strands-agent-factory integration:
- **config_converter.py**: YacbaConfig → AgentFactoryConfig
  - Field mapping: tool_configs_dir → tool_config_paths
  - Field mapping: files_to_upload → file_paths
  - Session path determination (sessions_home)
  - Initial message handling
  - Printer creation (auto vs plain)
  - Conversation manager type conversion

**adapters/repl_toolkit/** - repl-toolkit integration:
- **backend.py**: Backend protocol implementation
  - send_message() - delegates to AgentProxy
  - cancel() - interrupt tool execution
  - Async iteration of response streams
- **completer.py**: YacbaCompleter (file path completion)
- **actions/**: Interactive commands
  - **registry.py**: YacbaActionRegistry
  - **status_action.py**: /status command
  - **session_actions.py**: /save, /load commands
  - **info_actions.py**: /tools, /config commands

### Utilities Module

**utils/** - Helper functions:
- **file_utils.py**: Tool config discovery, file loading
  - discover_tool_configs() - Find .tools.json files
  - File glob expansion
- **config_utils.py**: Config file discovery/loading
  - discover_config_files() - Find .yacba/config.yaml
  - YAML/JSON/TOML parsing
- **model_config_parser.py**: Model config parsing with overrides
  - Load JSON model configs
  - Apply --mc key:value overrides
- **general_utils.py**: General utility functions
- **startup_messages.py**: Welcome messages, status display
  - print_welcome_message()
  - print_startup_info()
- **logging.py**: Centralized logging configuration (envlog)
  - get_logger() - Get module-specific logger with structlog-style support
  - PTHN_LOG environment variable (Rust RUST_LOG syntax)
  - Supports: `PTHN_LOG=error,yacba.config=debug,strands_agents=warn`

### Scripts Module

**scripts/** - Maintenance utilities:
- **fix_strands_session.py**: Session repair tool
  - Fixes corrupted session files
  - Documented in TROUBLESHOOTING.md

### Types Module

**yacba_types/** - Type definitions:
- **base.py**: ExitCode enum
- **config.py**: Configuration type aliases
- **content.py**: FileUpload, Message types

---

## Configuration System

### YacbaConfig Dataclass

All YACBA configuration in one place (source of truth):

```python
@dataclass
class YacbaConfig:
    # Common options (at top for --help)
    model_string: str
    system_prompt: str
    headless: bool
    initial_message: Optional[str]
    session_name: Optional[str]
    
    # Model configuration
    model_config: Dict[str, Any]
    emulate_system_prompt: bool
    disable_context_repair: bool
    
    # Conversation management
    conversation_manager_type: ConversationManagerType
    sliding_window_size: int
    preserve_recent_messages: int
    summary_ratio: float
    summarization_model: Optional[str]
    summarization_model_config: Dict[str, Any]
    custom_summarization_prompt: Optional[str]
    should_truncate_results: bool
    
    # File handling
    max_files: int
    
    # Session & agent
    agent_id: Optional[str]
    
    # Output & UI
    show_tool_use: bool
    cli_prompt: Optional[str]
    response_prefix: Optional[str]
    
    # Internal fields (cli_exclude)
    tool_config_paths: List[PathLike]
    startup_files_content: Optional[List[Message]]
    prompt_source: str
    files_to_upload: List[FileUpload]
    tool_configs_dir: Optional[str]
    tool_discovery_result: Optional[str]
```

**CLI Generation**:
- Arguments auto-generated via dataclass-args from field annotations
- Short aliases: `-m`, `-s`, `-H`, `-i`
- Boolean flags: `--flag` / `--no-flag`
- Dict overrides: `--mc key:value`
- File loading: `@file.txt` syntax for annotated fields
- Choices validation: conversation_manager_type restricted
- Field order determines --help output order

**Meta-Arguments** (not in dataclass, handled in factory.py):
- `--profile <name>` - Select profile from config file
- `--list-profiles` - Show available profiles
- `--show-config` - Display resolved configuration
- `--init-config <path>` - Generate sample config file
- `--config <path>` - Handled via dataclass-args base_configs
- `-h, --help` - Generated by dataclass-args

### Configuration Precedence (Detailed)

Implemented in `config/factory.py`:

1. **Parse meta-arguments** (--profile, --list-profiles, etc.)
   - Handle early-exit commands (--help, --list-profiles)
   
2. **Profile resolution** via profile-config
   - Loads: ARGUMENT_DEFAULTS → PROFILE → ENV VARS
   - Profile file: ./.yacba/config.yaml or ~/.yacba/config.yaml
   - Profile selection: --profile > YACBA_PROFILE > 'default'
   - Profile inheritance supported
   
3. **Manual @file.txt processing**
   - profile-config and env vars don't auto-load @file.txt
   - Manually process for: system_prompt, initial_message, etc.
   
4. **dataclass-args resolution** via base_configs
   - base_configs = profile_config (from step 2+3)
   - Adds --config file if specified
   - Adds CLI arguments (highest priority)
   
5. **YACBA post-processing**
   - Tool discovery (if tool_configs_dir specified)
   - Prompt source detection (CLI vs config vs default)
   - Creates new YacbaConfig with internal fields populated

### Profile Configuration Example

```yaml
# ~/.yacba/config.yaml
default_profile: development

defaults:
  conversation_manager_type: sliding_window
  sliding_window_size: 40
  max_files: 10

profiles:
  development:
    model_string: litellm:gemini/gemini-1.5-flash
    system_prompt: You are a helpful development assistant.
    tool_configs_dir: ~/.yacba/tools/
    show_tool_use: true
    
  production:
    inherits: development  # Profile inheritance
    model_string: openai:gpt-4
    system_prompt: @~/.yacba/prompts/production.txt
    conversation_manager_type: summarizing
    session_name: prod-session
```

Usage:
```bash
# Use development profile
yacba --profile development

# Use production profile via env var
export YACBA_PROFILE=production
yacba

# Override specific settings
yacba --profile development -m "anthropic:claude-3-sonnet"
```

### Environment Variables

All YACBA config fields can be set via `YACBA_*` environment variables:

```bash
export YACBA_MODEL_STRING="openai:gpt-4"
export YACBA_SYSTEM_PROMPT="You are an expert programmer"
export YACBA_SESSION_NAME="my-session"
export YACBA_SHOW_TOOL_USE="true"
export YACBA_PROFILE="production"

# Logging (Rust RUST_LOG syntax via PTHN_LOG)
export PTHN_LOG="error"                                    # All loggers at ERROR
export PTHN_LOG="error,yacba=info"                         # YACBA at INFO, rest ERROR
export PTHN_LOG="error,yacba.config=debug"                 # Fine-grained control
export PTHN_LOG="info,strands_agent_factory=warn"          # Suppress noisy libraries
```

---

## Adapter Pattern Implementation

### Config Conversion Adapter

**Purpose**: Convert YACBA configuration → strands-agent-factory configuration

```python
class YacbaToStrandsConfigConverter:
    def convert(self) -> AgentFactoryConfig:
        return AgentFactoryConfig(
            # Core
            model=self.yacba_config.model_string,
            system_prompt=self.yacba_config.system_prompt,
            model_config=self.yacba_config.model_config,
            emulate_system_prompt=self.yacba_config.emulate_system_prompt,
            disable_context_repair=self.yacba_config.disable_context_repair,
            
            # Initial state
            initial_message=self.yacba_config.initial_message,
            file_paths=self._convert_file_uploads(),  # List[Tuple[Path, mimetype]]
            
            # Tools
            tool_config_paths=self._convert_tool_configs(),  # List[Path]
            
            # Session
            session_id=self.yacba_config.session_name,
            sessions_home=self._get_sessions_home(),  # ~/.yacba/sessions or None
            
            # Conversation management
            conversation_manager_type=self._convert_conversation_manager_type(),
            sliding_window_size=self.yacba_config.sliding_window_size,
            preserve_recent_messages=self.yacba_config.preserve_recent_messages,
            summary_ratio=self.yacba_config.summary_ratio,
            summarization_model=self.yacba_config.summarization_model,
            summarization_model_config=self.yacba_config.summarization_model_config,
            custom_summarization_prompt=self.yacba_config.custom_summarization_prompt,
            should_truncate_results=self.yacba_config.should_truncate_results,            # Output
            show_tool_use=self.yacba_config.show_tool_use,
            response_prefix=auto_format(self.yacba_config.response_prefix),  # Pre-format to prevent XML parsing issues
            output_printer=print_formatted_text if not self.yacba_config.headless else print,
            
            # callback_handler not used by YACBA
        )
```

**Key Conversions**:
- `tool_configs_dir` (str) → `tool_config_paths` (List[Path])
- `files_to_upload` (various) → `file_paths` (List[Tuple[Path, Optional[str]]])
- `session_name` → `session_id` + `sessions_home` calculation
- `response_prefix` → Pre-formatted with `auto_format()` to prevent XML parsing issues
- Printer selection: `print_formatted_text` (interactive) vs `print` (headless)

### Backend Adapter

**Purpose**: Implement repl_toolkit Backend protocol using strands-agent-factory AgentProxy

```python
class YacbaBackend(Backend):
    def __init__(self, agent: AgentProxy, config: AgentFactoryConfig):
        self.agent = agent
        self.config = config
    
    async def send_message(self, message: str):
        # Delegate to strands-agent-factory
        async for event in self.agent.send_message_to_agent(message):
            # Convert strands event → repl_toolkit event
            yield self._convert_event(event)
    
    async def cancel(self):
        # Interrupt tool execution
        await self.agent.cancel()
```

**Event Conversion**:
- Strands events → repl_toolkit display format
- Handles: text chunks, tool calls, errors, completions

---

## Extension Points

### Adding New Configuration Options

1. Add field to `YacbaConfig` dataclass (config/dataclass.py)
   - Use appropriate dataclass-args annotations
   - Position in file determines --help order
2. Add default value to `ARGUMENT_DEFAULTS` (config/arguments.py)
3. (Optional) Add to `_build_env_vars()` for env var support
4. Add to `YacbaToStrandsConfigConverter.convert()` if needed by strands-agent-factory
5. Update documentation (README.md, API.md)

Example:
```python
# config/dataclass.py
@dataclass
class YacbaConfig:
    # ... other fields ...
    
    my_new_option: str = combine_annotations(
        cli_help("Description of my new option"),
        default="default_value")
```

### Adding New Commands

1. Create Action class in `adapters/repl_toolkit/actions/`
2. Register in `YacbaActionRegistry` (actions/registry.py)
3. Command automatically available in interactive mode

Example:
```python
# adapters/repl_toolkit/actions/my_action.py
class MyAction(Action):
    name = "/mycommand"
    help_text = "Do something custom"
    
    async def execute(self, backend, args):
        # Access agent via backend.agent
        # Access config via backend.config
        return "Custom action result"

# adapters/repl_toolkit/actions/registry.py
class YacbaActionRegistry:
    def __init__(self, printer):
        # ... existing actions ...
        self.register(MyAction(printer))
```

### Adding New Completers

1. Create Completer class (inherit from Completer protocol)
2. Add to merged completer in `yacba.py`

```python
# yacba.py in _run_interactive_mode
my_completer = MyCustomCompleter()
completer = merge_completers([
    command_completer,
    shell_completer,
    file_completer,
    my_completer  # Add here
])
```

### Adding New Meta-Arguments

1. Add to meta_parser in `config/factory.py` (`_parse_args_with_meta()`)
2. Add to filter in `_filter_meta_args()`
3. Add handling logic in `parse_config()`

Example:
```python
# config/factory.py
def _parse_args_with_meta():
    meta_parser = argparse.ArgumentParser(add_help=False)
    # ... existing meta-args ...
    meta_parser.add_argument('--my-meta-arg', type=str, default=None)
    # ...

def _filter_meta_args(argv):
    # ... existing filters ...
    if arg in ['--my-meta-arg']:
        skip_next = True
    # ...
```

### Extending Tool Support

**Note**: Tool types are defined by strands-agent-factory, not YACBA.

To add new tool types:
1. Implement in strands-agent-factory
2. YACBA automatically supports them (config passed through)

Current tool types (from strands-agent-factory):
- `python` - Python function tools (function decorators)
- `mcp` - MCP server tools (external processes)
- `a2a` - Agent-to-Agent tools (AI agents as tools)

### Adding Utility Modules

1. Create new module in `utils/`
2. Import and use in relevant components
3. Add unit tests in `tests/unit/`

Example:
```python
# utils/my_utils.py
def my_utility_function():
    pass

# Use in yacba.py or elsewhere
from utils.my_utils import my_utility_function
```

### Extending Logging

Logging uses envlog with Rust RUST_LOG-style syntax via `PTHN_LOG`:

```python
# Get module-specific logger
from utils.logging import get_logger
logger = get_logger(__name__)

# Traditional stdlib logging
logger.info("Operation completed")
logger.error("Operation failed", exc_info=True)

# Structlog-style (backward compatible)
logger.info("operation_completed", items=42, duration_ms=123)
logger.debug("user_action", user_id="abc", action="login")
```

Control logging via `PTHN_LOG` environment variable:
```bash
# Set default level for everything
export PTHN_LOG="error"

# Set per-module levels (Rust RUST_LOG syntax)
export PTHN_LOG="error,yacba=info"                         # YACBA at INFO
export PTHN_LOG="error,yacba.config=debug"                 # Fine-grained
export PTHN_LOG="info,strands_agent_factory=warn"          # Suppress noisy libs
export PTHN_LOG="debug"                                    # Everything at DEBUG
```

**Logging Features**:
- Single environment variable controls all logging (YACBA + third-party)
- Rust RUST_LOG syntax via envlog
- Backward compatible with structlog-style kwargs
- Standard library logging (no structlog dependency)

### Adding Session Repair Scripts

1. Create script in `scripts/` directory
2. Make executable: `chmod +x scripts/my_script.py`
3. Document in TROUBLESHOOTING.md
4. Use YACBA utilities (logging, config, etc.)

Example:
```python
#!/usr/bin/env python3
# scripts/my_repair_script.py
from utils.logging import get_logger
logger = get_logger(__name__)

def repair_something():
    logger.info("repair_started")
    # ... repair logic ...
    logger.info("repair_completed")

if __name__ == "__main__":
    repair_something()
```

---

## Testing Strategy

### Test Organization

```
code/tests/
├── __init__.py
├── conftest.py             # Pytest configuration, fixtures
├── config/                 # Config system tests
│   └── __init__.py
└── unit/                   # Unit tests
    ├── test_factory.py              # Config parsing
    ├── test_arguments.py            # Arguments and defaults
    ├── test_completer.py            # Tab completion
    ├── test_model_config_parser.py  # Model config parsing
    ├── test_config_utils.py         # Config utilities
    ├── test_general_utils.py        # General utilities
    ├── test_file_utils.py           # File utilities
    ├── test_config_converter.py     # Config conversion
    └── test_yacba_types.py          # Type definitions
```

### Unit Tests

Test individual components in isolation:

**Configuration Tests** (test_factory.py, test_arguments.py):
- Profile resolution
- Environment variable parsing
- CLI argument precedence
- Meta-argument handling
- @file.txt loading

**Conversion Tests** (test_config_converter.py):
- YacbaConfig → AgentFactoryConfig conversion
- Field mapping correctness
- Type conversions

**Utility Tests**:
- File discovery (test_file_utils.py)
- Config loading (test_config_utils.py)
- Model config parsing (test_model_config_parser.py)
- General utilities (test_general_utils.py)

**Completion Tests** (test_completer.py):
- File path completion
- Command completion
- Shell expansion

**Type Tests** (test_yacba_types.py):
- Exit codes
- Type aliases

### Running Tests

```bash
# All tests
cd code
pytest

# Specific test file
pytest tests/unit/test_factory.py

# With coverage
pytest --cov=. --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Integration Testing

Manual integration testing:

```bash
# Interactive mode
python code/yacba.py -m "gpt-4o"

# Headless mode
echo "Test message" | python code/yacba.py -H -m "gpt-4o"

# With profile
python code/yacba.py --profile development

# Show resolved config
python code/yacba.py --show-config

# List profiles
python code/yacba.py --list-profiles
```

### Test Fixtures (conftest.py)

Common fixtures for testing:
- Temporary config files
- Mock AgentProxy
- Sample tool configurations
- Mock REPL backend

---

## Performance Considerations

### Configuration Loading

- **Lazy loading**: Tool configs loaded on demand
- **Efficient parsing**: YAML parsing optimized (PyYAML)

### Completion System

- **Alphabetical sorting**: Commands sorted once at initialization
- **Lazy file listing**: Path completion computed on-demand
- **Shell timeout**: 2-second timeout prevents hanging

### Memory Management

**YACBA Layer**:
- Minimal memory footprint (thin wrapper)
- Config stored as dataclass (efficient)
- No large data structures maintained

**strands-agent-factory Layer**:
- Conversation management (sliding window, summarization)
- Tool result truncation (should_truncate_results)
- Session persistence to disk (not memory)

See [strands-agent-factory performance docs](https://github.com/bassmanitram/strands-agent-factory) for details.

### Logging Performance

- **Lazy evaluation**: Log messages only formatted if level enabled
- **Minimal overhead**: Standard library logging is efficient
- **Conditional formatting**: Structlog-style formatting only when logging occurs

---

## Security Considerations

### Input Validation

**YACBA Layer**:
- CLI argument validation (dataclass-args)
- Path traversal protection in file loading
- Environment variable expansion sanitization
- Profile inheritance cycle detection (profile-config)

**strands-agent-factory Layer**:
- Tool input validation
- LLM response sanitization

### Shell Expansion

**Risk**: `$(command)` expansion executes shell commands

**Mitigation**:
- Only executes on explicit Tab press
- 2-second timeout prevents hanging
- User fully controls execution
- Disabled in headless mode

### Configuration Files

- YAML/JSON parsing with error handling
- Environment variable expansion with sanitization
- Profile inheritance validated (no cycles)
- Config file permissions respected

### Session Persistence

**Session Storage**:
- Location: `~/.yacba/sessions/` or root `.strands-sessions/`
- File permissions: User-only read/write (0600)
- Contains conversation history
- May contain sensitive information

**Security Recommendations**:
- Don't share session directories
- Regular cleanup of old sessions
- Be aware sessions contain full conversation history
- Use `--session-name` to organize sessions

### API Keys

- Never commit to version control
- Store in environment variables
- Use profile-config for per-profile keys
- Don't log API keys (sanitized by strands-agent-factory)

### Tool Execution

**Python Tools**:
- Executed in same process (full system access)
- Trust only your own tool files

**MCP Tools**:
- Executed in separate processes
- Communicate via stdio
- Limited by MCP server permissions

**A2A Tools**:
- Calls to other AI agents
- API key required
- Rate limiting applies

---

## Deployment Architecture

### Standalone CLI

Most common deployment:
```bash
cd code
python yacba.py -m "gpt-4o"
```

**Requirements**:
- Python 3.8+
- pip install -r requirements.txt
- API keys in environment

### Container Deployment

Docker example:
```dockerfile
FROM python:3.11
WORKDIR /app
COPY code/requirements.txt .
RUN pip install -r requirements.txt
COPY code/ .
ENV OPENAI_API_KEY="..."
ENV PTHN_LOG="info"
CMD ["python", "yacba.py", "-H", "-i", "@/input/message.txt"]
```

### CI/CD Integration

Headless mode for automation:
```bash
# In CI pipeline
echo "Analyze code changes" | python code/yacba.py \
  -m "gpt-4o" \
  -H \
  --session-name "ci-run-${BUILD_ID}"
```

### Session Storage Locations

**Default Locations**:
- With --session-name: `~/.yacba/sessions/<session_name>.json`
- Root fallback: `./.strands-sessions/<session_id>.json`

**Configuration**:
- Controlled by strands-agent-factory
- YACBA passes: session_id, sessions_home
- Sessions_home: `~/.yacba/sessions` (if session_name set)

### Profile Configuration Locations

**Search Order** (profile-config):
1. `./.yacba/config.yaml` (project-specific)
2. `~/.yacba/config.yaml` (user-wide)

**Initialize Configuration**:
```bash
# Create sample config
yacba --init-config ~/.yacba/config.yaml

# Or project-specific
yacba --init-config ./.yacba/config.yaml
```

### Tool Configuration Discovery

**Automatic Discovery**:
```bash
yacba --tool-configs-dir ~/.yacba/tools/
```

Finds all `*.tools.json` files in directory.

**Example Structure**:
```
~/.yacba/
├── config.yaml                  # Profile configuration
├── tools/
│   ├── aws-cli.tools.json
│   ├── aws-doc.tools.json
│   ├── local-files.tools.json
│   └── python-tools.tools.json
├── sessions/                    # Session persistence
│   ├── dev-session.json
│   └── prod-session.json
└── prompts/                     # Custom prompts
    ├── development.txt
    └── production.txt
```

---

## Monitoring and Observability

### Logging

Uses envlog for environment-based logging configuration:

```bash
# Set default level for everything
export PTHN_LOG="error"

# Set per-module levels (Rust RUST_LOG syntax)
export PTHN_LOG="info"                                     # All at INFO
export PTHN_LOG="error,yacba=info"                         # YACBA at INFO, rest ERROR
export PTHN_LOG="error,yacba.config=debug"                 # Fine-grained control
export PTHN_LOG="info,strands_agent_factory=warn"          # Suppress noisy libs
export PTHN_LOG="debug"                                    # Everything at DEBUG

python code/yacba.py -m "gpt-4o"
```

**Log Levels**:
- **DEBUG**: Configuration details, adapter calls
- **INFO**: Major operations (agent creation, session load)
- **WARNING**: Recoverable issues (config missing, fallbacks)
- **ERROR**: Fatal errors (config invalid, tool failure)

**PTHN_LOG Syntax** (Rust RUST_LOG-style):
- `error` - Set all loggers to ERROR
- `error,yacba=info` - YACBA at INFO, rest at ERROR
- `error,yacba.config=debug` - Specific module override
- Comma-separated list of `module=level` pairs

### Debugging

Enable trace logging:
```bash
export PTHN_LOG="debug"
python code/yacba.py --show-config
```

Shows:
- Config precedence resolution
- Profile loading details
- Adapter conversions
- repl_toolkit events
- strands-agent-factory calls

### Configuration Inspection

```bash
# Show resolved configuration
yacba --show-config

# List available profiles
yacba --list-profiles

# Show help (all options)
yacba --help
```

---

## Related Documentation

### Internal
- [Main README](../README.md) - User guide, features, getting started
- [API Documentation](API.md) - YACBA's wrapper APIs
- [Completion System](COMPLETION_SYSTEM.md) - Tab completion architecture
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions

### External
- **[strands-agent-factory](https://github.com/bassmanitram/strands-agent-factory)** - Core architecture
  - Agent lifecycle and management
  - Tool system architecture
  - Conversation management design
  - Provider adapter pattern
- **[strands-agents](https://github.com/pydantic/strands-agents)** - Foundation architecture
- **[repl-toolkit](https://pypi.org/project/repl-toolkit/)** - REPL architecture
- **[dataclass-args](https://pypi.org/project/dataclass-args/)** - CLI generation
- **[profile-config](https://pypi.org/project/profile-config/)** - Configuration management
- **[envlog](https://pypi.org/project/envlog/)** - Environment-based logging

---

## Glossary

- **AgentProxy**: strands-agent-factory's agent interface for message handling
- **AgentFactory**: strands-agent-factory's agent creator
- **AgentFactoryConfig**: Configuration format for strands-agent-factory
- **Backend**: repl_toolkit protocol for message handling
- **YacbaConfig**: YACBA's configuration dataclass (source of truth)
- **YacbaBackend**: YACBA's implementation of repl_toolkit Backend protocol
- **YacbaActionRegistry**: Registry of interactive commands (/status, /tools, etc.)
- **Adapter**: Bridge between different abstractions (config, backend)
- **A2A**: Agent-to-Agent (AI agents as tools)
- **MCP**: Model Context Protocol (tool servers)
- **profile-config**: Library for configuration profile management
- **dataclass-args**: Library for auto-generating CLI from dataclasses
- **repl-toolkit**: Library for building interactive REPLs
- **HeadlessREPL**: Non-interactive mode (stdin → stdout)
- **AsyncREPL**: Interactive mode (with completion, history, formatting)
- **meta-arguments**: Arguments not in YacbaConfig (--profile, --list-profiles, etc.)
- **base_configs**: dataclass-args parameter for configuration precedence
- **printer abstraction**: Output handler (auto-format vs plain)
- **context manager**: Agent lifecycle management (with agent as ctx)
- **envlog**: Environment-based logging configuration (Rust RUST_LOG syntax)
- **PTHN_LOG**: Environment variable for logging configuration

---

## Version History

### v2.0 (Current)
- **Wrapper architecture**: YACBA as thin CLI wrapper over strands-agent-factory
- **Profile system**: profile-config integration for configuration management
- **Improved CLI**: dataclass-args for automatic CLI generation
- **Meta-arguments**: --profile, --list-profiles, --show-config, --init-config
- **Modular completion**: Separate completers for commands, shell, files
- **Session repair**: fix_strands_session.py utility
- **Simplified logging**: envlog with PTHN_LOG (Rust RUST_LOG syntax)
- **HeadlessREPL**: Improved non-interactive mode

### v1.0
- **Monolithic architecture**: All functionality in YACBA
- **Direct strands-agents integration**: No factory abstraction
- **Manual CLI parsing**: argparse without dataclass-args
- **Basic config files**: Limited profile support

---

Last Updated: 2024-12-05  
Architecture Version: 2.0
