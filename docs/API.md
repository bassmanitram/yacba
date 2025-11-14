# YACBA API Documentation

Complete API reference for YACBA's wrapper layer - the CLI, configuration, and adapter components.

> **Note**: This documents **YACBA's wrapper APIs only**. For strands-agent-factory APIs  
> (agent creation, tool development, conversation management, A2A tools), see the  
> [strands-agent-factory documentation](https://github.com/JBarmentlo/strands-agent-factory).

---

## What YACBA Provides

YACBA is a thin wrapper that adds:

- **Configuration Management** - YacbaConfig dataclass with precedence system
- **CLI Parsing** - Auto-generated via dataclass-args
- **Interactive REPL** - Via repl-toolkit with completion
- **Configuration Profiles** - Via profile-config
- **Adapters** - Bridge YACBA config → strands-agent-factory config

**Core agent functionality** (LLM integration, tool execution, conversation management) is in  
[strands-agent-factory](https://github.com/JBarmentlo/strands-agent-factory).

---

## Table of Contents

1. [Configuration System](#configuration-system)
2. [Adapters](#adapters)
   - [strands_factory Adapter](#strandsfactory-adapter)
   - [repl_toolkit Adapters](#repltoolkit-adapters)
3. [Utilities](#utilities)
4. [Type Definitions](#type-definitions)
5. [Constants](#constants)
6. [Completion System](#completion-system)

---

## Configuration System

### Module: `config`

The configuration module provides dataclass-based configuration management with multi-source precedence and validation.

#### `YacbaConfig`

Main configuration dataclass containing all YACBA settings.

```python
@dataclass
class YacbaConfig:
    # Core settings
    model_string: Optional[str]
    system_prompt: Optional[str]
    emulate_system_prompt: bool
    headless: bool
    initial_message: Optional[str]
    
    # Tool configuration
    tool_configs_dir: Optional[str]
    files_to_upload: List[Tuple[str, str]]
    max_files: int
    
    # Model configuration
    model_config: Optional[str]
    config_overrides: List[str]
    summarization_model_config: Optional[str]
    summarization_config_overrides: List[str]
    
    # Session management
    session_name: Optional[str]
    agent_id: Optional[str]
    
    # Conversation management
    conversation_manager_type: str
    window_size: int
    preserve_recent_messages: int
    summary_ratio: float
    summarization_model: Optional[str]
    custom_summarization_prompt: Optional[str]
    truncate_tool_results: bool
    
    # UI configuration
    cli_prompt: Optional[str]
    response_prefix: Optional[str]
    show_tool_use: bool
    
    # Configuration file management
    profile: Optional[str]
    config_file: Optional[str]
    list_profiles: bool
    show_config: bool
    init_config: Optional[str]
```

**Key Properties**:
- Immutable after creation (frozen dataclass)
- Validated on instantiation
- Supports environment variable expansion
- Profile-based configuration support
- CLI arguments auto-generated via dataclass-args

---

#### `parse_config() -> YacbaConfig`

Parse configuration from multiple sources with precedence.

**Returns**: Fully resolved `YacbaConfig` instance

**Precedence** (highest to lowest):
1. CLI arguments
2. User-specified config file (`--config-file`)
3. Discovered config files (`~/.yacba/config.yaml`, `./yacba.yaml`)
4. Environment variables
5. Default values

**Example**:
```python
from config import parse_config

# Parse from CLI args (uses sys.argv)
config = parse_config()

# Access configuration
print(config.model_string)
print(config.conversation_manager_type)
```

**Note**: CLI arguments are automatically generated from the YacbaConfig dataclass using  
[dataclass-args](https://pypi.org/project/dataclass-args/).

---

## Adapters

### strands_factory Adapter

#### Module: `adapters.strands_factory.config_converter`

##### `YacbaToStrandsConfigConverter`

Converts YACBA configuration to strands-agent-factory configuration format.

```python
class YacbaToStrandsConfigConverter:
    def __init__(self, yacba_config: YacbaConfig)
    def convert() -> Dict[str, Any]
```

**Methods**:

###### `__init__(yacba_config: YacbaConfig)`

Initialize converter with YACBA configuration.

**Parameters**:
- `yacba_config`: The YACBA configuration to convert

---

###### `convert() -> Dict[str, Any]`

Convert YACBA config to strands-agent-factory format.

**Returns**: Dictionary compatible with `strands_agent_factory.AgentFactory` configuration

**Conversion Mapping**:
- `model_string` → `model`
- `system_prompt` → `system_prompt`
- `conversation_manager_type` → `conversation_manager_type`
- `tool_configs_dir` → `tool_config_paths`
- `files_to_upload` → `file_paths`
- Model parameters → `model_config`
- Summarization config → `summarization_model_config`

**Example**:
```python
from config import parse_config
from adapters.strands_factory import YacbaToStrandsConfigConverter

yacba_config = parse_config()
converter = YacbaToStrandsConfigConverter(yacba_config)
strands_config = converter.convert()

# Use with AgentFactory
from strands_agent_factory import AgentFactory
factory = AgentFactory(config=strands_config)
```

**See Also**: [strands-agent-factory AgentFactory docs](https://github.com/JBarmentlo/strands-agent-factory)

---

### repl_toolkit Adapters

#### Module: `adapters.repl_toolkit.backend`

##### `YacbaBackend`

Backend adapter that implements repl_toolkit's backend protocol using strands-agent-factory agents.

```python
class YacbaBackend(Backend):
    def __init__(self, agent: AgentProxy, config: Dict[str, Any])
    async def send_message(self, message: str) -> AsyncIterator[Dict[str, Any]]
    async def cancel()
```

**Methods**:

###### `__init__(agent: AgentProxy, config: Dict[str, Any])`

Initialize backend with strands-agent-factory agent and configuration.

**Parameters**:
- `agent`: strands_agent_factory AgentProxy instance
- `config`: Converted configuration dictionary

---

###### `async send_message(message: str) -> AsyncIterator[Dict[str, Any]]`

Send a message and stream responses from the agent.

**Parameters**:
- `message`: User message text

**Returns**: Async iterator of response events

**Event Types**:
- `{'type': 'text', 'content': str}` - Text response chunk
- `{'type': 'tool_use', 'name': str, 'input': dict}` - Tool execution
- `{'type': 'tool_result', 'result': Any}` - Tool result
- `{'type': 'error', 'error': str}` - Error message

**Example**:
```python
async for event in backend.send_message("Hello"):
    if event['type'] == 'text':
        print(event['content'], end='')
```

---

###### `async cancel()`

Cancel the current operation.

**Example**:
```python
await backend.cancel()  # Cancels running message processing
```

---

#### Module: `adapters.repl_toolkit.completer`

##### `YacbaCompleter`

File path completion for `file()` syntax. Command and shell expansion are handled by repl_toolkit's built-in completers.

```python
class YacbaCompleter(Completer):
    def __init__()
    def get_completions(self, document, complete_event) -> Iterable[Completion]
```

**Methods**:

###### `__init__()`

Initialize the file path completer.

**Note**: YacbaCompleter only handles `file()` path completion:
- **Command completion** (`/help`, `/status`) → repl_toolkit's `PrefixCompleter`
- **Shell expansion** (`${VAR}`, `$(cmd)`) → repl_toolkit's `ShellExpansionCompleter`
- **File paths** (`file("path")`) → `YacbaCompleter` (this class)

---

###### `get_completions(document, complete_event) -> Iterable[Completion]`

Get file path completions for `file()` syntax.

**Parameters**:
- `document`: The current document
- `complete_event`: The completion event

**Returns**: Iterable of `Completion` objects for file paths

**Completion Context**:
- Triggered inside `file("...")` or `file('...')` syntax
- Supports tilde expansion (`~/`)
- Supports absolute and relative paths

**Example**:
```python
# In interactive mode:
file("/tmp/<Tab>     # Completes to files in /tmp
file("~/Doc<Tab>     # Completes to ~/Documents
```

**See Also**: [Completion System](#completion-system) for full completion architecture

---

#### Module: `adapters.repl_toolkit.actions.registry`

##### `YacbaActionRegistry`

Action registry that integrates YACBA-specific actions with repl-toolkit.

```python
class YacbaActionRegistry(ActionRegistry):
    def __init__()
    def list_commands() -> List[str]
```

**Methods**:

###### `__init__()`

Initialize registry with YACBA-specific actions.

**Registered Actions**:
- Status and information commands (`/status`, `/info`, `/stats`)
- Session management commands (`/session`)
- Conversation management commands (`/conversation-manager`, `/conversation-stats`)
- Tool commands (`/tools`)
- History commands (`/history`, `/clear`)

---

###### `list_commands() -> List[str]`

Get list of all available command names.

**Returns**: List of command strings (e.g., `["/help", "/exit", "/status"]`)

**Note**: Commands are returned **unsorted**. The caller should sort them for display purposes  
(YACBA sorts them alphabetically in the PrefixCompleter for better UX).

**Example**:
```python
registry = YacbaActionRegistry()
commands = sorted(registry.list_commands())  # Sort for display
print(commands)
# ['/clear', '/conversation-manager', '/exit', '/help', ...]
```

---

#### Module: `adapters.repl_toolkit.actions.status_action`

##### `StatusAction`

Action for displaying comprehensive session status.

```python
class StatusAction(Action):
    async def execute(self, backend: Backend, args: Optional[str]) -> str
```

**Methods**:

###### `async execute(backend: Backend, args: Optional[str]) -> str`

Execute status display action.

**Parameters**:
- `backend`: The backend instance
- `args`: Optional arguments (not used)

**Returns**: Formatted status string

**Status Information**:
- Model configuration
- System prompt
- Conversation manager settings
- Session information
- Tool count
- Message count

**Example**:
```python
# In interactive mode:
/status
# Shows comprehensive session status
```

---

#### Module: `adapters.repl_toolkit.actions.info_actions`

Contains utility actions for displaying information.

##### `ToolsAction`

Display available tools.

```python
class ToolsAction(Action):
    async def execute(self, backend: Backend, args: Optional[str]) -> str
```

**Note**: Tools are managed by strands-agent-factory. See [strands-agent-factory tool docs](https://github.com/JBarmentlo/strands-agent-factory#tools).

---

##### `ConversationStatsAction`

Display conversation statistics.

```python
class ConversationStatsAction(Action):
    async def execute(self, backend: Backend, args: Optional[str]) -> str
```

---

#### Module: `adapters.repl_toolkit.actions.session_actions`

Contains session management actions.

##### `SessionAction`

Session save/load/list operations.

```python
class SessionAction(Action):
    async def execute(self, backend: Backend, args: Optional[str]) -> str
```

**Subcommands**:
- `save [name]` - Save current session
- `load <name>` - Load saved session
- `list` - List saved sessions

**Example**:
```python
# In interactive mode:
/session save my-session    # Save session
/session load my-session    # Load session
/session list               # List all sessions
```

**Note**: Session persistence is handled by strands-agent-factory.

---

##### `ConversationManagerAction`

Change conversation management strategy.

```python
class ConversationManagerAction(Action):
    async def execute(self, backend: Backend, args: Optional[str]) -> str
```

**Arguments**:
- `null` - Disable conversation management
- `sliding_window` - Use sliding window strategy
- `summarizing` - Use summarization strategy

**Example**:
```python
# In interactive mode:
/conversation-manager sliding_window
/conversation-manager summarizing
```

**Note**: Conversation management is implemented by strands-agent-factory. See  
[strands-agent-factory conversation management docs](https://github.com/JBarmentlo/strands-agent-factory).

---

## Utilities

### Module: `utils.file_utils`

#### `discover_tool_configs(directory: str) -> List[Dict[str, Any]]`

Discover and parse tool configuration files in a directory.

**Parameters**:
- `directory`: Path to directory containing tool configs

**Returns**: List of parsed tool configuration dictionaries

**Supported Formats**:
- `.json` - JSON configuration files
- `.yaml`, `.yml` - YAML configuration files

**Tool Configuration Format**: Defined by strands-agent-factory. Supports:
- `type: "python"` - Python function tools
- `type: "mcp"` - MCP server tools
- `type: "a2a"` - Agent-to-Agent tools

**Example**:
```python
from utils.file_utils import discover_tool_configs

configs = discover_tool_configs("./sample-tool-configs")
for config in configs:
    print(config['tools'])
```

**See Also**:
- [strands-agent-factory tool configuration](https://github.com/JBarmentlo/strands-agent-factory#tools)
- Sample configs in `sample-tool-configs/` directory

---

#### `load_file_content(path: str, mimetype: str) -> Dict[str, Any]`

Load file content with appropriate processing based on mimetype.

**Parameters**:
- `path`: File path (supports globs)
- `mimetype`: MIME type of the file

**Returns**: Dictionary with file content and metadata

**Supported Types**:
- Text files: `text/plain`, `text/markdown`, etc.
- PDF: `application/pdf`
- Images: `image/png`, `image/jpeg`, etc.
- Documents: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`

---

### Module: `utils.model_config_parser`

#### `ModelConfigParser`

Parser for model configuration files with JSON-like syntax.

```python
class ModelConfigParser:
    @staticmethod
    def parse_file(path: str) -> Dict[str, Any]
    
    @staticmethod
    def parse_string(content: str) -> Dict[str, Any]
```

**Methods**:

##### `parse_file(path: str) -> Dict[str, Any]`

Parse model configuration from file.

**Parameters**:
- `path`: Path to configuration file

**Returns**: Parsed configuration dictionary

**Supported Syntax**:
- JSON format
- Comments: `//` and `/* */`
- Trailing commas
- Environment variable expansion: `${VAR}`

**Example**:
```python
from utils.model_config_parser import ModelConfigParser

config = ModelConfigParser.parse_file("sample-model-configs/openai-gpt4.json")
print(config['temperature'])
```

---

##### `parse_string(content: str) -> Dict[str, Any]`

Parse model configuration from string.

**Parameters**:
- `content`: Configuration string

**Returns**: Parsed configuration dictionary

---

#### `parse_model_config(path: str, overrides: List[str]) -> Dict[str, Any]`

Parse model configuration with CLI overrides.

**Parameters**:
- `path`: Configuration file path
- `overrides`: List of override strings (e.g., `["temperature:0.7", "max_tokens:1000"]`)

**Returns**: Merged configuration dictionary

**Override Format**:
- Simple: `key:value`
- Nested: `key.nested:value`
- Type conversion: Automatic (string, int, float, bool)

**Example**:
```python
from utils.model_config_parser import parse_model_config

config = parse_model_config(
    "sample-model-configs/openai-gpt4.json",
    ["temperature:0.7", "max_tokens:2000"]
)
```

**CLI Usage**:
```bash
python yacba.py -m "gpt-4o" --model-config config.json --mc temperature:0.9
```

---

### Module: `utils.config_utils`

#### `discover_config_files() -> List[str]`

Discover configuration files in standard locations.

**Returns**: List of found configuration file paths

**Search Locations**:
1. `~/.yacba/config.yaml`
2. `~/.yacba/config.yml`
3. `~/.yacba/config.json`
4. `./yacba.yaml`
5. `./yacba.yml`
6. `./yacba.json`

**Note**: Uses profile-config for configuration management.

---

#### `load_config_file(path: str) -> Dict[str, Any]`

Load and parse configuration file.

**Parameters**:
- `path`: Configuration file path

**Returns**: Parsed configuration dictionary

**Supported Formats**:
- YAML (`.yaml`, `.yml`)
- JSON (`.json`)

---

#### `merge_configs(base: Dict, override: Dict) -> Dict`

Deep merge two configuration dictionaries.

**Parameters**:
- `base`: Base configuration
- `override`: Override configuration

**Returns**: Merged configuration

**Behavior**:
- Nested dictionaries are recursively merged
- Lists are replaced (not merged)
- Override values take precedence

---

### Module: `utils.startup_messages`

#### `print_startup_info(...)`

Print formatted startup information.

**Parameters**:
- `model_id`: Model identifier
- `system_prompt`: System prompt text
- `prompt_source`: Source of the prompt
- `tools`: List of available tools
- `startup_files`: Files loaded at startup
- `conversation_manager_info`: Conversation manager details

**Example**:
```python
from utils.startup_messages import print_startup_info

print_startup_info(
    model_id="gpt-4o",
    system_prompt="You are a helpful assistant",
    prompt_source="CLI argument",
    tools=agent.tool_specs,
    startup_files=config.files_to_upload,
    conversation_manager_info="Sliding Window (size=40)"
)
```

---

#### `print_welcome_message()`

Print ASCII art welcome message.

---

## Type Definitions

### Module: `yacba_types`

#### `ExitCode`

Exit code enumeration.

```python
class ExitCode(IntEnum):
    SUCCESS = 0
    USER_INTERRUPT = 130
    CONFIGURATION_ERROR = 1
    RUNTIME_ERROR = 2
    FATAL_ERROR = 3
```

---

#### `ContentType`

Content type enumeration for file uploads.

```python
class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
```

---

## Constants

### Module: `config.constants`

#### Environment Variables

- `YACBA_CONFIG`: Path to configuration file
- `YACBA_PROFILE`: Profile to use
- `YACBA_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

#### Configuration Defaults

```python
DEFAULT_WINDOW_SIZE = 40
DEFAULT_PRESERVE_RECENT = 10
DEFAULT_SUMMARY_RATIO = 0.3
DEFAULT_MAX_FILES = 10
DEFAULT_CLI_PROMPT = "User: "
DEFAULT_RESPONSE_PREFIX = "Assistant: "
```

---

## Completion System

### Overview

YACBA uses a modular completion system with three types of completers merged together:

1. **PrefixCompleter** (from repl-toolkit) - Command completion
2. **ShellExpansionCompleter** (from repl-toolkit) - Variable/command expansion
3. **YacbaCompleter** (YACBA-specific) - File path completion

### Integration

Completers are merged in `yacba.py`:

```python
from prompt_toolkit.completion import merge_completers
from repl_toolkit.completion import PrefixCompleter, ShellExpansionCompleter
from adapters.repl_toolkit.completer import YacbaCompleter

# Create individual completers
command_completer = PrefixCompleter(
    words=sorted(action_registry.list_commands()),
    prefix='/',
    ignore_case=True
)

shell_completer = ShellExpansionCompleter(
    timeout=2.0,
    multiline_all=True,
    max_lines=30
)

file_completer = YacbaCompleter()

# Merge for unified completion
completer = merge_completers([
    command_completer,
    shell_completer,
    file_completer
])
```

### Completion Examples

**Command Completion**:
```
/he<Tab> → /help
/co<Tab> → /clear, /conversation-manager, /conversation-stats
```

**File Path Completion**:
```
file("/tmp/<Tab> → /tmp/.ICE-unix, /tmp/.Test-unix, ...
file("~/Doc<Tab> → ~/Documents/
```

**Shell Variable Expansion**:
```
${HOME}<Tab> → /home/username
${XDG_CONFIG_HOME}<Tab> → /home/username/.config
```

**Shell Command Expansion**:
```
$(whoami)<Tab> → jbartle9
$(date)<Tab> → Mon Jan  6 15:23:45 PST 2025
```

**See Also**: [Completion System Documentation](COMPLETION_SYSTEM.md) for detailed architecture

---

## Error Handling

### Configuration Errors

Raised when configuration is invalid:
```python
raise ConfigurationError("Invalid model string: must specify provider")
```

### Runtime Errors

Raised during execution:
```python
raise RuntimeError("Failed to initialize agent factory")
```

### Tool Loading Errors

Raised when tool configurations are invalid:
```python
raise ToolLoadingError("Invalid tool configuration: missing 'type' field")
```

**Note**: Tool loading is handled by strands-agent-factory. See  
[strands-agent-factory error handling](https://github.com/JBarmentlo/strands-agent-factory).

---

## Testing

### Unit Tests

Test individual components:
```bash
PYTHONPATH=code python -c "
from config import parse_config
from adapters.strands_factory import YacbaToStrandsConfigConverter
# Test configuration parsing
"
```

### Integration Tests

Test component interaction:
```bash
python -m pytest code/tests/
```

### Manual Testing

```bash
# Test completion
python code/yacba.py -m "gpt-4o"
# Then press Tab in different contexts

# Test configuration
python code/yacba.py --show-config --profile development
```

---

## Related Documentation

### Internal
- [Main README](../README.md) - Feature overview and quick start
- [Architecture](ARCHITECTURE.md) - System design and patterns
- [Completion System](COMPLETION_SYSTEM.md) - Tab completion details
- [Troubleshooting](TROUBLESHOOTING.md) - Problem solving

### External
- **[strands-agent-factory](https://github.com/JBarmentlo/strands-agent-factory)** - Core agent APIs
  - Agent creation and lifecycle
  - Tool development (Python, MCP, A2A)
  - Conversation management strategies
  - Provider configuration
- **[strands-agents](https://github.com/pydantic/strands-agents)** - Underlying framework
- **[repl-toolkit](https://github.com/your-org/repl-toolkit)** - REPL framework APIs
- **[dataclass-args](https://pypi.org/project/dataclass-args/)** - CLI parsing
- **[profile-config](https://pypi.org/project/profile-config/)** - Configuration management

---

## Version Information

- **YACBA Version**: 2.0+ (Wrapper Architecture)
- **strands-agent-factory Version**: 1.1.1+
- **repl-toolkit Version**: 1.2.0+
- **dataclass-args Version**: 1.1.0+
- **API Documentation Version**: 2.0
- **Last Updated**: 2025-01-15

---

## See Also

- [Architecture Documentation](ARCHITECTURE.md) - System design
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Problem solving
- [Main README](../README.md) - Feature overview
- [strands-agent-factory Documentation](https://github.com/JBarmentlo/strands-agent-factory) - Core agent features
