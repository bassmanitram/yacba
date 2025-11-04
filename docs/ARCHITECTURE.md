# YACBA Architecture Documentation

## Overview

YACBA is a **CLI wrapper** built on top of [strands-agent-factory](https://github.com/JBarmentlo/strands-agent-factory), which itself is built on [strands-agents](https://github.com/pydantic/strands-agents).

**YACBA's Role**: Provide command-line interface, configuration management, and interactive REPL on top of strands-agent-factory's core agent functionality.

**Core Functionality** (LLM integration, tool execution, conversation management, A2A support) comes from strands-agent-factory.

> **Note**: This documents YACBA's wrapper architecture only. For core agent architecture,  
> see [strands-agent-factory documentation](https://github.com/JBarmentlo/strands-agent-factory).

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
9. [Performance Considerations](#performance-considerations)

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
- Command-line interface
- Configuration profiles
- Interactive REPL with completion
- Headless automation mode
- Configuration file discovery
- Glob pattern file loading

---

## Component Diagrams

### Package Structure

```
yacba/
├── code/
│   ├── yacba.py                    # Main entry point, orchestration
│   ├── config/                     # Configuration system
│   │   ├── arguments.py            # CLI argument definitions
│   │   ├── dataclass.py            # YacbaConfig dataclass
│   │   └── factory.py              # Configuration parsing/merging
│   ├── adapters/                   # Adapter implementations
│   │   ├── strands_factory/        # strands-agent-factory adapters
│   │   │   └── config_converter.py # YACBA config → strands config
│   │   └── repl_toolkit/           # repl-toolkit adapters
│   │       ├── backend.py          # Backend protocol implementation
│   │       ├── completer.py        # File path completion
│   │       └── actions/            # Interactive commands
│   │           ├── registry.py     # Command registry
│   │           ├── status_action.py
│   │           ├── session_actions.py
│   │           └── info_actions.py
│   ├── utils/                      # Utility modules
│   │   ├── file_utils.py           # File/tool config discovery
│   │   ├── config_utils.py         # Config file loading
│   │   ├── model_config_parser.py  # Model config parsing
│   │   └── startup_messages.py     # Welcome/info display
│   └── yacba_types/                # Type definitions
│       ├── base.py                 # Exit codes
│       ├── config.py               # Config types
│       └── content.py              # Content types
├── sample-tool-configs/            # Example tool configurations
│   ├── strands.tools.json          # Python function tools
│   ├── aws-cli.tools.json          # MCP server tools
│   └── a2a-example.tools.json      # A2A (Agent-to-Agent) tools
└── sample-model-configs/           # Example model configurations
    ├── openai-gpt4.json
    ├── anthropic-claude.json
    └── litellm-gemini.json
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
│  (YacbaConfig)  │
└──────┬──────────┘
       │ YacbaConfig
       ▼
┌─────────────────────────┐
│  YacbaToStrands         │
│  ConfigConverter        │
└──────┬──────────────────┘
       │ strands config dict
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

Configuration precedence (highest to lowest):

```
┌─────────────────┐
│  CLI Arguments  │  ← Highest priority
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  --config-file  │  ← User-specified config
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Discovered     │  ← ~/.yacba/config.yaml, ./yacba.yaml
│  Config Files   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Environment    │  ← YACBA_CONFIG, YACBA_PROFILE
│  Variables      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Default Values │  ← Lowest priority
└─────────────────┘
```

**Implementation**:
- CLI parsing via dataclass-args (auto-generated from YacbaConfig)
- Profile loading via profile-config
- Merging via config/factory.py

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
           │  AgentProxy      │  (strands-agent-factory)
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
           │  (display)       │
           └────────┬─────────┘
                    │
                    ▼
                User sees output
```

---

## Design Patterns

### 1. Adapter Pattern

YACBA uses adapters to bridge between different abstractions:

**YacbaToStrandsConfigConverter**:
- Converts YacbaConfig (YACBA's format) → strands-agent-factory config dict
- Handles field name mapping, type conversion, defaults

**YacbaBackend**:
- Implements repl_toolkit's Backend protocol
- Delegates to strands-agent-factory AgentProxy
- Converts between repl_toolkit events and strands response streams

**YacbaActionRegistry**:
- Implements repl_toolkit's ActionRegistry
- Provides YACBA-specific commands (/status, /tools, etc.)

### 2. Protocol-Based Design

Uses protocols (interfaces) for loose coupling:

```python
# repl_toolkit defines protocols
class Backend(Protocol):
    async def send_message(self, message: str) -> AsyncIterator[Dict]: ...
    async def cancel(self): ...

# YACBA implements protocol
class YacbaBackend(Backend):
    def __init__(self, agent: AgentProxy, config: Dict):
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
config = parse_config()  # YacbaConfig
converter = YacbaToStrandsConfigConverter(config)
strands_config = converter.convert()

factory = AgentFactory(config=strands_config)  # Inject config
agent = factory.create_agent()

backend = YacbaBackend(agent, strands_config)  # Inject agent
repl = AsyncREPL(backend=backend, ...)  # Inject backend
```

### 4. Strategy Pattern

Conversation management uses strategy pattern (in strands-agent-factory):

```python
# User selects strategy via YACBA config
config.conversation_manager_type = "sliding_window"  # or "summarizing", "null"

# strands-agent-factory applies strategy
# YACBA just passes the configuration through
```

---

## Module Structure

### Core Entry Point

**yacba.py** - Main orchestration:
```python
def main():
    config = parse_config()  # Parse CLI + files
    asyncio.run(_run_agent_lifecycle(config))

async def _run_agent_lifecycle(config):
    # Convert config
    strands_config = YacbaToStrandsConfigConverter(config).convert()
    
    # Create agent (via strands-agent-factory)
    factory = AgentFactory(config=strands_config)
    await factory.initialize()
    agent = factory.create_agent()
    
    # Run appropriate mode
    if config.headless:
        await _run_headless_mode(agent, ...)
    else:
        await _run_interactive_mode(agent, ...)
```

### Configuration Module

**config/** - Configuration management:
- **dataclass.py**: YacbaConfig dataclass (CLI auto-generated via dataclass-args)
- **factory.py**: parse_config() - Merge CLI + files + env + defaults
- Uses profile-config for profile management

### Adapters Module

**adapters/strands_factory/** - strands-agent-factory integration:
- **config_converter.py**: YacbaConfig → strands config dict

**adapters/repl_toolkit/** - repl-toolkit integration:
- **backend.py**: Backend protocol implementation
- **completer.py**: File path completion (commands via PrefixCompleter)
- **actions/**: Interactive commands

### Utilities Module

**utils/** - Helper functions:
- **file_utils.py**: Tool config discovery, file loading
- **config_utils.py**: Config file discovery/loading
- **model_config_parser.py**: Model config parsing with overrides
- **startup_messages.py**: Welcome messages, status display

---

## Configuration System

### YacbaConfig Dataclass

All YACBA configuration in one place:

```python
@dataclass
class YacbaConfig:
    # Model
    model_string: Optional[str]
    model_config: Optional[str]
    
    # System
    system_prompt: Optional[str]
    emulate_system_prompt: bool
    
    # Tools & Files
    tool_configs_dir: Optional[str]
    files_to_upload: List[Tuple[str, str]]
    
    # Conversation
    conversation_manager_type: str
    sliding_window_size: int
    preserve_recent_messages: int
    summary_ratio: float
    summarization_model: Optional[str]
    
    # Session
    session_name: Optional[str]
    agent_id: Optional[str]
    
    # UI
    headless: bool
    cli_prompt: Optional[str]
    response_prefix: Optional[str]
    show_tool_use: bool
    
    # Config Management
    profile: Optional[str]
    config_file: Optional[str]
```

CLI arguments **auto-generated** via dataclass-args from this dataclass.

### Configuration Precedence

Implemented in `config/factory.py`:

1. **parse_config()** orchestrates precedence
2. **profile-config** handles profile loading
3. **dataclass-args** handles CLI parsing
4. Explicit merging for environment variables

---

## Adapter Pattern Implementation

### Config Conversion Adapter

**Purpose**: Convert YACBA configuration → strands-agent-factory configuration

```python
class YacbaToStrandsConfigConverter:
    def convert(self) -> Dict[str, Any]:
        return {
            'model': self.config.model_string,
            'system_prompt': self.config.system_prompt,
            'conversation_manager_type': self.config.conversation_manager_type,
            'tool_config_paths': self._get_tool_paths(),
            'file_paths': self.config.files_to_upload,
            # ... etc
        }
```

**Mapping**:
- YACBA field names → strands-agent-factory field names
- Handle defaults, conversions, nested structures

### Backend Adapter

**Purpose**: Implement repl_toolkit Backend protocol using strands-agent-factory AgentProxy

```python
class YacbaBackend(Backend):
    async def send_message(self, message: str):
        async for event in self.agent.send_message_to_agent(message):
            # Convert strands event → repl_toolkit event
            yield self._convert_event(event)
    
    async def cancel(self):
        # Delegate to agent
        await self.agent.cancel()
```

---

## Extension Points

### Adding New Configuration Options

1. Add field to `YacbaConfig` dataclass
2. CLI argument auto-generated via dataclass-args
3. Add to `YacbaToStrandsConfigConverter.convert()` if needed
4. Update defaults in `config/dataclass.py`

### Adding New Commands

1. Create Action class in `adapters/repl_toolkit/actions/`
2. Register in `YacbaActionRegistry`
3. Command automatically available in interactive mode

Example:
```python
class MyAction(Action):
    name = "/mycommand"
    help_text = "Do something custom"
    
    async def execute(self, backend, args):
        return "Custom action result"
```

### Adding New Completers

1. Create Completer class
2. Add to merged completer in `yacba.py`

```python
my_completer = MyCustomCompleter()
completer = merge_completers([
    command_completer,
    shell_completer,
    file_completer,
    my_completer  # Add here
])
```

### Extending Tool Support

**Note**: Tool types are defined by strands-agent-factory, not YACBA.

To add new tool types:
1. Implement in strands-agent-factory
2. YACBA automatically supports them (just passes config through)

Current tool types (from strands-agent-factory):
- `python` - Python function tools
- `mcp` - MCP server tools
- `a2a` - Agent-to-Agent tools

---

## Performance Considerations

### Configuration Loading

- **Lazy loading**: Tool configs loaded on demand
- **Caching**: Config files cached after first load
- **Profile-config**: Efficient YAML parsing

### Completion System

- **Alphabetical sorting**: Commands sorted once at initialization
- **Lazy file listing**: Path completion computed on-demand
- **Shell timeout**: 2-second timeout prevents hanging

### Memory Management

**YACBA Layer**:
- Minimal memory footprint (thin wrapper)
- Config stored as dataclass (efficient)

**strands-agent-factory Layer**:
- Conversation management (sliding window, summarization)
- Tool result truncation
- Session persistence to disk

See [strands-agent-factory performance docs](https://github.com/JBarmentlo/strands-agent-factory) for details.

---

## Security Considerations

### Input Validation

**YACBA Layer**:
- CLI argument validation (dataclass-args)
- Path traversal protection in file loading
- Environment variable expansion sanitization

**strands-agent-factory Layer**:
- Tool input validation
- LLM response sanitization

### Shell Expansion

**Risk**: `$(command)` expansion executes shell commands

**Mitigation**:
- Only executes on explicit Tab press
- 2-second timeout
- User fully controls execution

### Configuration Files

- YAML/JSON parsing with schema validation
- Environment variable expansion with sanitization
- Profile inheritance checked for cycles

---

## Testing Strategy

### Unit Tests

Test individual components in isolation:
- Config parsing
- Config conversion
- Adapter methods

### Integration Tests

Test component interaction:
- Config → strands config conversion
- Backend → agent communication
- Complete message flow

### Manual Testing

Interactive testing:
```bash
python code/yacba.py -m "gpt-4o"  # Interactive mode
python code/yacba.py --show-config  # Config display
python code/yacba.py -H -i "test"  # Headless mode
```

---

## Deployment Architecture

### Standalone CLI

Most common deployment:
```
user@machine:~$ python yacba.py -m "gpt-4o"
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
CMD ["python", "yacba.py", "-H", "-i", "..."]
```

### CI/CD Integration

Headless mode for automation:
```bash
# In CI pipeline
python code/yacba.py \
  -m "gpt-4o" \
  -H \
  -i "Analyze code changes" \
  -f "*.py" "text/plain"
```

---

## Monitoring and Observability

### Logging

Uses loguru for structured logging:
```bash
export LOGURU_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
python code/yacba.py -m "gpt-4o"
```

**Log Levels**:
- **DEBUG**: Configuration details, adapter calls
- **INFO**: Major operations (agent creation, session load)
- **WARNING**: Recoverable issues
- **ERROR**: Fatal errors

### Debugging

Enable trace logging:
```bash
export LOGURU_LEVEL=TRACE
python code/yacba.py --show-config
```

Shows:
- Config precedence resolution
- Adapter conversions
- repl_toolkit events
- strands-agent-factory calls

---

## Related Documentation

### Internal
- [API Documentation](API.md) - YACBA's wrapper APIs
- [Completion System](COMPLETION_SYSTEM.md) - Tab completion architecture
- [Troubleshooting](TROUBLESHOOTING.md) - Problem solving
- [Main README](../README.md) - Feature overview

### External
- **[strands-agent-factory](https://github.com/JBarmentlo/strands-agent-factory)** - Core architecture
  - Agent lifecycle and management
  - Tool system architecture
  - Conversation management design
  - Provider adapter pattern
- **[strands-agents](https://github.com/pydantic/strands-agents)** - Foundation architecture
- **[repl-toolkit](https://github.com/your-org/repl-toolkit)** - REPL architecture
- **[dataclass-args](https://pypi.org/project/dataclass-args/)** - CLI generation
- **[profile-config](https://pypi.org/project/profile-config/)** - Configuration management

---

## Version History

- **v2.0**: Wrapper architecture (current)
  - YACBA as thin CLI wrapper
  - strands-agent-factory integration
  - Modular completion system
  
- **v1.0**: Monolithic architecture
  - All functionality in YACBA
  - Direct strands-agents integration

---

## Glossary

- **AgentProxy**: strands-agent-factory's agent interface
- **AgentFactory**: strands-agent-factory's agent creator
- **Backend**: repl_toolkit protocol for message handling
- **YacbaConfig**: YACBA's configuration dataclass
- **Adapter**: Bridge between different abstractions
- **A2A**: Agent-to-Agent (AI agents as tools)
- **MCP**: Model Context Protocol (tool servers)

---

Last Updated: 2025-01-06  
Architecture Version: 2.0
