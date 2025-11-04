# YACBA Architecture Documentation

## Overview

YACBA (Yet Another ChatBot Agent) is built on a **modular, adapter-based architecture** that separates concerns across three specialized packages:

1. **YACBA Core** - Configuration, CLI, orchestration
2. **strands-agent-factory** - Agent lifecycle, tools, AI integration
3. **repl-toolkit** - Interactive/headless UI

This document provides comprehensive architectural documentation including diagrams, design patterns, and component interactions.

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

---

## High-Level Architecture

### System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                         YACBA System                            │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  YACBA Core  │───▶│   strands-   │───▶│     repl-    │       │
│  │              │    │    agent-    │    │    toolkit   │       │
│  │ • Config     │    │   factory    │    │              │       │
│  │ • CLI        │    │              │    │ • Interactive│       │
│  │ • Files      │    │ • Agent      │    │ • Headless   │       │
│  │ • Orchestr.  │    │ • Tools      │    │ • Commands   │       │
│  └──────────────┘    │ • AI Provs   │    └──────────────┘       │
│                      └──────────────┘                           │
│                                                                 │
│  External Dependencies:                                         │
│  • strands-agents (AI framework)                                │
│  • LiteLLM (100+ AI providers)                                  │
│  • prompt_toolkit (terminal UI)                                 │
│  • profile-config (configuration management)                    │
└─────────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Separation of Concerns** - Each package handles its domain
2. **Adapter Pattern** - Clean interfaces between components
3. **Dependency Inversion** - Depend on abstractions, not implementations
4. **Single Responsibility** - Each module has one clear purpose
5. **Open/Closed** - Open for extension, closed for modification

---

## Component Diagrams

### Package Structure

```
yacba/
├── code/
│   ├── yacba.py                    # Main entry point
│   ├── config/                     # Configuration system
│   │   ├── arguments.py            # CLI argument definitions
│   │   ├── dataclass.py            # YacbaConfig dataclass
│   │   └── factory.py              # Configuration orchestration
│   ├── adapters/                   # Adapter implementations
│   │   ├── strands_factory/        # strands-agent-factory adapters
│   │   │   └── config_converter.py # Config conversion
│   │   └── repl_toolkit/           # repl-toolkit adapters
│   │       ├── backend.py          # Backend protocol implementation
│   │       ├── completer.py        # Tab completion
│   │       └── actions/            # Command actions
│   │           ├── registry.py     # Action registry
│   │           ├── session_actions.py # Session commands
│   │           ├── info_actions.py # Info commands
│   │           └── status_action.py # Status command
│   ├── utils/                      # Utility modules
│   │   ├── config_utils.py         # Tool discovery
│   │   ├── file_utils.py           # File operations
│   │   ├── model_config_parser.py  # Model config parsing
│   │   └── startup_messages.py     # Startup display
│   └── yacba_types/                # Type definitions
│       ├── base.py                 # Base types
│       ├── config.py               # Config types
│       └── content.py              # Content types
└── docs/                           # Documentation
```

---

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          User Interface                             │
│                     (Terminal / Script)                             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         yacba.py (Main)                             │
│  • Parse CLI arguments                                              │
│  • Initialize configuration                                         │
│  • Create agent lifecycle                                           │
│  • Select mode (interactive/headless)                               │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Configuration System                             │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ config.factory.parse_config()                                │   │
│  │  1. Parse CLI args (config.arguments)                        │   │
│  │  2. Load env vars                                            │   │
│  │  3. Discover config files (./.yacba, ~/.yacba)               │   │
│  │  4. Merge with precedence (profile-config)                   │   │
│  │  5. Validate (config.dataclass)                              │   │
│  │  6. Return YacbaConfig                                       │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Config Conversion                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ YacbaToStrandsConfigConverter                                │   │
│  │  • Convert YacbaConfig → AgentFactoryConfig                  │   │
│  │  • Map tool paths                                            │   │
│  │  • Map file uploads                                          │   │
│  │  • Map conversation settings                                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    strands-agent-factory                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ AgentFactory                                                 │   │
│  │  • Initialize with AgentFactoryConfig                        │   │
│  │  • Load tools (Python functions, MCP servers)                │   │
│  │  • Create AI model connection                                │   │
│  │  • Setup conversation manager                                │   │
│  │  • Return AgentProxy                                         │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Backend Adapter                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ YacbaBackend (implements AsyncBackend)                       │   │
│  │  • Wrap AgentProxy                                           │   │
│  │  • Implement handle_input()                                  │   │
│  │  • Provide agent access for commands                         │   │
│  │  • Store AgentFactoryConfig for status                       │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        repl-toolkit                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ AsyncREPL / HeadlessREPL                                     │   │
│  │  • Interactive: prompt_toolkit UI                            │   │
│  │  • Headless: direct message processing                       │   │
│  │  • Command system (/status, /clear, etc.)                    │   │
│  │  • Tab completion (alphabetically sorted)                    │   │
│  │  • History management                                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Configuration Flow

```
CLI Arguments
    │
    ├─▶ parse_args() ──────────────────────┐
    │                                      │
Environment Variables                      │
    │                                      │
    └─▶ ARGUMENTS_FROM_ENV_VARS ───────────┤
                                           │
Discovered Config Files                    │
    │                                      │
    ├─▶ ./.yacba/config.yaml ──────────────┤
    └─▶ ~/.yacba/config.yaml ──────────────┤
                                           │
User Config File                           │
    │                                      │
    └─▶ --config-file ─────────────────────┤
                                           │
                                           ▼
                                    ┌───────────────┐
                                    │ profile-config│
                                    │   resolver    │
                                    │  (precedence) │
                                    └───────┬───────┘
                                            │
                                            ▼
                                    ┌───────────────┐
                                    │  validate_args│
                                    └───────┬───────┘
                                            │
                                            ▼
                                    ┌───────────────┐
                                    │  YacbaConfig  │
                                    └───────────────┘
```

### Message Flow (Interactive Mode)

```
User Input
    │
    ▼
┌─────────────────┐
│ prompt_toolkit  │
│   (AsyncREPL)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ YacbaBackend    │
│ handle_input()  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AgentProxy     │
│ send_message()  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ strands-agents  │
│   Agent.run()   │
└────────┬────────┘
         │
         ├─▶ AI Provider (OpenAI, Anthropic, etc.)
         │       │
         │       ▼
         │   Response
         │       │
         ├─▶ Tool Execution (if needed)
         │       │
         │       ▼
         │   Tool Results
         │       │
         └───────┘
         │
         ▼
┌─────────────────┐
│ Callback Handler│
│  (auto-printer) │
└────────┬────────┘
         │
         ▼
    Terminal Output
```

### Command Flow (/status example)

```
User Types "/status"
         │
         ▼
┌─────────────────┐
│ AsyncREPL       │
│ parse_command() │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│YacbaActionRegistry│
│ execute_action() │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ handle_status() │
│ (status_action) │
└────────┬────────┘
         │
         ├─▶ Get backend info
         ├─▶ Get agent proxy
         ├─▶ Get tool specs
         ├─▶ Get conversation stats
         └─▶ Format with rich
         │
         ▼
┌─────────────────┐
│ Rich Console    │
│ Status Panel    │
└─────────────────┘
```

### Tool Discovery Flow

```
--tool-configs-dir <dir>
         │
         ▼
┌─────────────────────────┐
│ discover_tool_configs() │
└────────┬────────────────┘
         │
         ├─▶ Scan directory for *.json, *.yaml
         │
         ├─▶ Validate each file
         │
         └─▶ Return (paths, ToolDiscoveryResult)
         │
         ▼
┌─────────────────────────┐
│  YacbaConfig            │
│  tool_config_paths      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ YacbaToStrandsConfig    │
│ Converter               │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ AgentFactoryConfig      │
│ tool_config_paths       │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ AgentFactory            │
│ • Load Python functions │
│ • Start MCP servers     │
│ • Register tools        │
└─────────────────────────┘
```

---

## Design Patterns

### 1. Adapter Pattern

**Purpose**: Bridge between incompatible interfaces

**Implementation**:

```python
# YacbaBackend adapts AgentProxy to AsyncBackend protocol
class YacbaBackend(AsyncBackend):
    def __init__(self, agent_proxy: AgentProxy, config: Optional[AgentFactoryConfig] = None):
        self.agent_proxy = agent_proxy
        self.config = config
    
    async def handle_input(self, user_input: str) -> bool:
        # Adapt repl-toolkit's interface to strands-agent-factory
        return await self.agent_proxy.send_message_to_agent(user_input)
```

**Benefits**:
- Clean separation between packages
- Easy to swap implementations
- Testable in isolation

---

### 2. Factory Pattern

**Purpose**: Centralize object creation

**Implementation**:

```python
# AgentFactory creates configured agents
factory = AgentFactory(config=strands_config)
await factory.initialize()
agent = factory.create_agent()
```

**Benefits**:
- Encapsulates complex initialization
- Consistent agent creation
- Easy to extend with new agent types

---

### 3. Strategy Pattern

**Purpose**: Select algorithm at runtime

**Implementation**:

```python
# Conversation management strategies
conversation_manager_type: Literal["null", "sliding_window", "summarizing"]

# Selected at runtime based on configuration
if config.conversation_manager_type == "sliding_window":
    # Use sliding window strategy
elif config.conversation_manager_type == "summarizing":
    # Use summarizing strategy
```

**Benefits**:
- Flexible conversation management
- Easy to add new strategies
- Runtime selection

---

### 4. Command Pattern

**Purpose**: Encapsulate requests as objects

**Implementation**:

```python
# Action registry with command objects
class YacbaActionRegistry(ActionRegistry):
    def __init__(self):
        super().__init__()
        register_session_actions(self)  # /session save, /session load
        register_info_actions(self)     # /info, /tools
        register_status_actions(self)   # /status, /stats, /info aliases
```

**Benefits**:
- Extensible command system
- Easy to add new commands
- Decoupled from UI

---

### 5. Dependency Injection

**Purpose**: Invert control of dependencies

**Implementation**:

```python
# Backend receives agent proxy and config via constructor
backend = YacbaBackend(agent_proxy, strands_config)

# REPL receives backend via run()
await repl.run(backend=backend)
```

**Benefits**:
- Testable components
- Flexible configuration
- Loose coupling

---

## Module Structure

### Configuration System

```
config/
├── arguments.py          # CLI argument definitions
│   ├── ArgumentDefinition (dataclass)
│   ├── ARGUMENT_DEFINITIONS (list of all args)
│   ├── ARGUMENT_DEFAULTS (default values)
│   ├── ARGUMENTS_FROM_ENV_VARS (env var mapping)
│   ├── parse_args() → Namespace
│   └── validate_args(config) → Dict
│
├── dataclass.py          # Configuration dataclass
│   ├── YacbaConfig (dataclass)
│   │   ├── Core fields (model, prompt, tools, files)
│   │   ├── Optional fields (session, conversation mgmt)
│   │   ├── Properties (has_session, is_interactive, etc.)
│   │   └── Validation (__post_init__)
│   └── ConversationManagerType (Literal)
│
└── factory.py            # Configuration orchestration
    ├── parse_config() → YacbaConfig
    │   ├── Parse CLI args
    │   ├── Load env vars
    │   ├── Discover config files
    │   ├── Merge with profile-config
    │   ├── Parse model configs
    │   ├── Discover tools
    │   └── Create YacbaConfig
    └── _filter_cli_overrides(args) → Dict
```

**Responsibilities**:
- Parse all configuration sources
- Merge with proper precedence
- Validate configuration
- Provide typed configuration object

---

### Adapters

```
adapters/
├── strands_factory/
│   └── config_converter.py
│       └── YacbaToStrandsConfigConverter
│           ├── __init__(yacba_config)
│           ├── convert() → AgentFactoryConfig
│           ├── _convert_tool_configs()
│           ├── _convert_file_uploads()
│           ├── _get_sessions_home()
│           ├── _build_initial_message()
│           └── _convert_conversation_manager_type()
│
└── repl_toolkit/
    ├── backend.py
    │   └── YacbaBackend (AsyncBackend)
    │       ├── __init__(agent_proxy, config)
    │       ├── handle_input(user_input) → bool
    │       ├── get_agent_proxy() → AgentProxy
    │       ├── clear_conversation() → bool
    │       ├── get_tool_names() → list[str]
    │       └── get_conversation_stats() → dict
    │
    ├── completer.py
    │   └── YacbaCompleter (Completer)
    │       ├── __init__(meta_commands) [sorts alphabetically]
    │       ├── get_completions(document, event)
    │       ├── add_command(command) [maintains sort]
    │       └── remove_command(command)
    │
    └── actions/
        ├── registry.py
        │   └── YacbaActionRegistry (ActionRegistry)
        │       └── __init__()
        │
        ├── session_actions.py
        │   └── register_session_actions(registry)
        │       ├── /session save <name>
        │       └── /session load <name>
        │
        ├── info_actions.py
        │   └── register_info_actions(registry)
        │       ├── /tools
        │       └── /clear
        │
        └── status_action.py
            └── register_status_actions(registry)
                ├── /status (main command)
                ├── /info (alias)
                └── /stats (alias)
```

**Responsibilities**:
- Bridge YACBA ↔ strands-agent-factory
- Bridge YACBA ↔ repl-toolkit
- Implement protocols
- Provide command system
- Status reporting with rich formatting

---

### Utilities

```
utils/
├── config_utils.py
│   └── discover_tool_configs(dir) → (paths, result)
│
├── file_utils.py
│   ├── validate_file_path(path) → bool
│   ├── load_file_content(path, type) → str
│   ├── resolve_glob(pattern) → list[str]
│   └── get_file_size(path) → int
│
├── model_config_parser.py
│   ├── ModelConfigParser
│   │   ├── load_config_file(path) → dict
│   │   ├── parse_property_override(override) → (path, value)
│   │   ├── apply_property_override(config, path, value)
│   │   ├── merge_configs(base, overrides) → dict
│   │   └── validate_model_config(config)
│   └── parse_model_config(file, overrides) → dict
│
└── startup_messages.py
    ├── print_startup_info(...)
    └── print_welcome_message()
```

**Responsibilities**:
- Tool discovery
- File operations
- Model config parsing
- Startup display

---

## Configuration System

### Configuration Precedence

```
Priority  Source                          Example
────────  ──────────────────────────────  ─────────────────────────
1 (Low)   Default values                  ARGUMENT_DEFAULTS
2         Environment variables           YACBA_MODEL_ID=gpt-4o
3         Discovered config files         ~/.yacba/config.yaml
4         User-specified config file      --config-file custom.yaml
5 (High)  CLI arguments                   --model gpt-4o
```

### Configuration Resolution

```python
# 1. Start with defaults
config = ARGUMENT_DEFAULTS.copy()

# 2. Apply environment variables
config.update(ARGUMENTS_FROM_ENV_VARS)

# 3. Apply discovered config files (via profile-config)
config.update(discovered_config)

# 4. Apply user-specified config file
if cli_args.config_file:
    config.update(load_config(cli_args.config_file))

# 5. Apply CLI arguments (highest priority)
config.update(cli_overrides)

# 6. Validate
config = validate_args(config)

# 7. Create YacbaConfig
return YacbaConfig(**config)
```

### Profile System

```yaml
# ~/.yacba/config.yaml
default_profile: development

defaults:
  conversation_manager: sliding_window
  window_size: 40

profiles:
  development:
    model: "litellm:gemini/gemini-2.5-flash"
    tool_configs_dir: "./dev-tools"
    show_tool_use: true
  
  production:
    inherits: development  # Inherit from development
    model: "anthropic:claude-3-5-sonnet"
    show_tool_use: false
```

**Usage**:
```bash
yacba --profile production
```

---

## Adapter Pattern Implementation

### Config Converter Adapter

**Purpose**: Convert YacbaConfig → AgentFactoryConfig

```python
class YacbaToStrandsConfigConverter:
    """
    Converts YACBA's rich configuration to strands-agent-factory's
    simpler AgentFactoryConfig format.
    """
    
    def convert(self) -> AgentFactoryConfig:
        return AgentFactoryConfig(
            # Map YACBA fields to strands-agent-factory fields
            model=self.yacba_config.model_string,
            system_prompt=self.yacba_config.system_prompt,
            tool_config_paths=self._convert_tool_configs(),
            file_paths=self._convert_file_uploads(),
            output_printer=create_auto_printer(),  # Auto-format responses
            # ... more mappings
        )
```

**Mapping Table**:

| YacbaConfig Field | AgentFactoryConfig Field | Transformation |
|-------------------|--------------------------|----------------|
| `model_string` | `model` | Direct |
| `system_prompt` | `system_prompt` | Direct |
| `tool_config_paths` | `tool_config_paths` | Convert to Path objects |
| `files_to_upload` | `file_paths` | Convert to (Path, mimetype) tuples |
| `session_name` | `session_id` | Direct |
| `conversation_manager_type` | `conversation_manager_type` | Direct |

---

### Backend Adapter

**Purpose**: Implement repl-toolkit's AsyncBackend protocol using strands-agent-factory's AgentProxy

```python
class YacbaBackend(AsyncBackend):
    """
    Adapts AgentProxy to AsyncBackend protocol.
    """
    
    def __init__(self, agent_proxy: AgentProxy, config: Optional[AgentFactoryConfig] = None):
        self.agent_proxy = agent_proxy
        self.config = config  # Store for status reporting
    
    async def handle_input(self, user_input: str) -> bool:
        # Translate repl-toolkit's interface to strands-agent-factory
        return await self.agent_proxy.send_message_to_agent(
            user_input,
            show_user_input=False
        )
```

**Protocol Implementation**:

| AsyncBackend Method | Implementation | Purpose |
|---------------------|----------------|---------|
| `handle_input(str)` | `agent_proxy.send_message_to_agent()` | Process user input |
| `is_ready` | Check agent_proxy existence | Readiness check |
| `clear_conversation()` | `agent_proxy.clear_messages()` | Clear history |
| `get_tool_names()` | `agent_proxy.tool_specs` | List tools (extracts names) |
| `get_conversation_stats()` | Access agent messages | Get stats |

---

## Extension Points

### 1. Adding New CLI Arguments

**Location**: `code/config/arguments.py`

```python
# Add to ARGUMENT_DEFINITIONS list
ArgumentDefinition(
    names=["--my-new-arg"],
    help="Description of new argument",
    argname="my_new_arg",
    validator=_validate_my_arg,  # Optional
)

# Add to ARGUMENT_DEFAULTS if needed
ARGUMENT_DEFAULTS["my_new_arg"] = "default_value"
```

**Update**:
1. Add to `YacbaConfig` dataclass in `config/dataclass.py`
2. Add to `AgentFactoryConfig` mapping in `adapters/strands_factory/config_converter.py`

---

### 2. Adding New Commands

**Location**: `code/adapters/repl_toolkit/actions/`

```python
# Create new action file: my_actions.py
def register_my_actions(registry: ActionRegistry):
    @registry.register_action("/mycommand")
    async def my_command(backend: AsyncBackend, args: str):
        """My custom command"""
        # Implementation
        return True

# Register in registry.py
from .my_actions import register_my_actions

class YacbaActionRegistry(ActionRegistry):
    def __init__(self):
        super().__init__()
        register_my_actions(self)  # Add this line
```

**Commands are automatically sorted alphabetically in tab completion.**

---

### 3. Adding New Conversation Strategies

**Location**: strands-agent-factory (external package)

YACBA delegates conversation management to strands-agent-factory. To add new strategies:

1. Implement in strands-agent-factory
2. Add to `ConversationManagerType` literal in YACBA
3. Update converter to handle new type

---

### 4. Adding New Tool Types

**Location**: strands-agent-factory (external package)

YACBA delegates tool management to strands-agent-factory. To add new tool types:

1. Implement in strands-agent-factory
2. Create tool configuration format
3. Place config files in tool directory
4. YACBA will auto-discover via `discover_tool_configs()`

---

## Performance Considerations

### Configuration Loading

- **Lazy Loading**: Config files loaded only when needed
- **Caching**: profile-config caches resolved configurations
- **Validation**: Early validation prevents runtime errors

### Message Processing

- **Async I/O**: All I/O operations are async
- **Streaming**: Responses streamed to terminal
- **Cancellation**: Support for Alt+C to cancel operations

### Memory Management

- **Conversation Strategies**: Automatic context window management
- **Tool Result Truncation**: Large results truncated to fit context
- **Session Persistence**: Efficient file-based storage

### Tab Completion

- **Alphabetical Sorting**: Commands sorted once at initialization
- **Efficient Lookup**: O(n) prefix matching for command completion
- **Context Awareness**: File completion in file() syntax

---

## Security Considerations

### Input Validation

- CLI arguments validated via validators
- File paths validated before access
- Model config validated before use

### Environment Variables

- Sensitive data (API keys) via environment variables
- Not logged or displayed
- Passed securely to AI providers

### File Access

- File paths resolved and validated
- Glob patterns restricted to specified directories
- Mimetype validation for uploads

---

## Testing Strategy

### Unit Tests

- Test each module in isolation
- Mock external dependencies
- Focus on business logic

### Integration Tests

- Test adapter interactions
- Test configuration flow
- Test command system

### End-to-End Tests

- Test full CLI workflows
- Test interactive mode
- Test headless mode

---

## Deployment Architecture

### Local Development

```
Developer Machine
├── Python 3.10+
├── Virtual Environment
│   ├── YACBA
│   ├── strands-agent-factory
│   ├── repl-toolkit
│   └── Dependencies
└── Configuration
    ├── ./.yacba/config.yaml
    └── ~/.yacba/config.yaml
```

### Production Deployment

```
Production Server
├── Container (Docker)
│   ├── Python Runtime
│   ├── YACBA + Dependencies
│   └── Configuration
├── Environment Variables
│   ├── YACBA_MODEL_ID
│   ├── API Keys
│   └── Session Storage
└── Monitoring
    ├── Logs (loguru)
    └── Metrics
```

---

## See Also

- [API Documentation](API.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Configuration Guide](../README.CONFIG.md)
- [Model Configuration Guide](../README.MODEL_CONFIG.md)