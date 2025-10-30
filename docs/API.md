# YACBA API Documentation

## Overview

This document provides comprehensive API documentation for YACBA's core modules, classes, and functions.

---

## Table of Contents

1. [Configuration System](#configuration-system)
2. [Adapters](#adapters)
3. [Utilities](#utilities)
4. [Type Definitions](#type-definitions)
5. [Main Entry Point](#main-entry-point)

---

## Configuration System

### Module: `config.arguments`

#### `ArgumentDefinition`

**Dataclass** for defining CLI arguments.

```python
@dataclass
class ArgumentDefinition:
    names: List[str]              # Argument names (e.g., ["-m", "--model"])
    argname: str                  # Destination name in parsed args
    help: str                     # Help text
    argtype: Optional[type]       # Argument type
    action: Optional[str]         # Argparse action (e.g., "append", "store_true")
    choices: Optional[List[str]]  # Valid choices
    nargs: Optional[Union[str, int]]  # Number of arguments
    validator: Optional[Callable] # Validation function
    default: Optional[Any]        # Default value
```

**Example**:
```python
ArgumentDefinition(
    names=["-m", "--model"],
    help="The model to use",
    argname="model",
)
```

---

#### `parse_args() -> Namespace`

Parse command-line arguments.

**Returns**: `argparse.Namespace` with parsed arguments

**Example**:
```python
from config.arguments import parse_args
args = parse_args()
print(args.model)  # Access parsed model argument
```

---

#### `validate_args(config: Dict[str, Any]) -> Dict[str, Any]`

Validate and convert argument values using their validators.

**Parameters**:
- `config`: Dictionary of configuration values

**Returns**: Validated configuration dictionary

**Raises**: `ValueError` if validation fails

**Example**:
```python
from config.arguments import validate_args
config = {"model": "gpt-4o", "max_files": "10"}
validated = validate_args(config)
# validated["max_files"] is now int(10)
```

---

#### Constants

**`ARGUMENT_DEFINITIONS`**: List of all CLI argument definitions (30 arguments)

**`ARGUMENT_DEFAULTS`**: Default values for arguments
```python
{
    "model": "litellm:gemini/gemini-2.5-flash",
    "system_prompt": "You are a general assistant...",
    "max_files": "10",
    "conversation_manager": "sliding_window",
    "window_size": "40",
    # ... more defaults
}
```

**`ARGUMENTS_FROM_ENV_VARS`**: Arguments loaded from environment variables
```python
{
    "model": os.environ.get("YACBA_MODEL_ID"),
    "system_prompt": os.environ.get("YACBA_SYSTEM_PROMPT"),
    "session": os.environ.get("YACBA_SESSION_NAME"),
}
```

---

### Module: `config.dataclass`

#### `YacbaConfig`

**Dataclass** representing YACBA's complete configuration.

```python
@dataclass
class YacbaConfig:
    # Core configuration
    model_string: str
    system_prompt: str
    prompt_source: str
    tool_config_paths: List[PathLike]
    startup_files_content: Optional[List[Message]]
    
    # Optional configuration with defaults
    headless: bool = False
    model_config: dict = field(default_factory=dict)
    summarization_model_config: dict = field(default_factory=dict)
    session_name: Optional[str] = None
    agent_id: Optional[str] = None
    emulate_system_prompt: bool = False
    show_tool_use: bool = False
    cli_prompt: Optional[str] = None
    response_prefix: Optional[str] = None
    initial_message: Optional[str] = None
    max_files: int = 20
    files_to_upload: List[FileUpload] = field(default_factory=list)
    tool_discovery_result: Optional[ToolDiscoveryResult] = None
    
    # Conversation management
    conversation_manager_type: ConversationManagerType = "sliding_window"
    sliding_window_size: int = 40
    preserve_recent_messages: int = 10
    summary_ratio: float = 0.3
    summarization_model: Optional[str] = None
    custom_summarization_prompt: Optional[str] = None
    should_truncate_results: bool = True
```

**Properties**:

- `has_startup_files: bool` - Check if startup files are configured
- `has_tool_configs: bool` - Check if tool configs are configured
- `framework_name: str` - Extract framework name from model string
- `model_name: str` - Extract model name from model string
- `is_interactive: bool` - Check if running in interactive mode
- `has_session: bool` - Check if session persistence is enabled
- `uses_conversation_manager: bool` - Check if conversation management is enabled
- `uses_sliding_window: bool` - Check if using sliding window
- `uses_summarizing: bool` - Check if using summarizing

**Example**:
```python
from config.dataclass import YacbaConfig

config = YacbaConfig(
    model_string="gpt-4o",
    system_prompt="You are a helpful assistant",
    prompt_source="cli",
    tool_config_paths=[],
    startup_files_content=None
)

print(config.framework_name)  # "litellm" (default)
print(config.is_interactive)  # True (headless=False)
```

---

### Module: `config.factory`

#### `parse_config() -> YacbaConfig`

Main configuration parsing entry point. Coordinates all configuration sources with proper precedence.

**Configuration Precedence** (lowest to highest):
1. Default values
2. Environment variables
3. Discovered config files (`./.yacba/config.yaml`, `~/.yacba/config.yaml`)
4. `--config-file` (user-specified override)
5. CLI arguments

**Returns**: Fully validated `YacbaConfig` object

**Raises**: `SystemExit` on configuration errors

**Example**:
```python
from config.factory import parse_config

# Parse configuration from all sources
config = parse_config()

# Access configuration
print(config.model_string)
print(config.tool_config_paths)
```

---

## Adapters

### Module: `adapters.strands_factory.config_converter`

#### `YacbaToStrandsConfigConverter`

Converts YACBA configuration to strands_agent_factory configuration.

```python
class YacbaToStrandsConfigConverter:
    def __init__(self, yacba_config: YacbaConfig)
    def convert(self) -> AgentFactoryConfig
```

**Methods**:

##### `__init__(yacba_config: YacbaConfig)`

Initialize the converter.

**Parameters**:
- `yacba_config`: The parsed YACBA configuration object

---

##### `convert() -> AgentFactoryConfig`

Convert YACBA configuration to AgentFactoryConfig.

**Returns**: `AgentFactoryConfig` for strands_agent_factory

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

---

### Module: `adapters.repl_toolkit.backend`

#### `YacbaBackend`

Adapter that wraps strands_agent_factory AgentProxy to implement repl_toolkit's AsyncBackend protocol.

```python
class YacbaBackend(AsyncBackend):
    def __init__(self, agent_proxy: AgentProxy)
    async def handle_input(self, user_input: str) -> bool
    def get_agent_proxy(self) -> AgentProxy
    def clear_conversation(self) -> bool
    def get_tool_names(self) -> list[str]
    def get_conversation_stats(self) -> dict
```

**Methods**:

##### `__init__(agent_proxy: AgentProxy)`

Initialize the backend adapter.

**Parameters**:
- `agent_proxy`: The strands_agent_factory AgentProxy instance

---

##### `async handle_input(user_input: str) -> bool`

Handle user input by processing it through the agent.

**Parameters**:
- `user_input`: The input string from the user

**Returns**: `True` if processing was successful, `False` otherwise

**Example**:
```python
backend = YacbaBackend(agent_proxy)
success = await backend.handle_input("Hello, how are you?")
```

---

##### `get_agent_proxy() -> AgentProxy`

Get the underlying AgentProxy instance.

**Returns**: The wrapped agent proxy instance

---

##### `clear_conversation() -> bool`

Clear the conversation history.

**Returns**: `True` if successful, `False` otherwise

---

##### `get_tool_names() -> list[str]`

Get list of available tool names.

**Returns**: List of tool names

---

##### `get_conversation_stats() -> dict`

Get conversation statistics.

**Returns**: Dictionary with statistics:
```python
{
    "message_count": int,
    "tool_count": int
}
```

---

### Module: `adapters.repl_toolkit.completer`

#### `YacbaCompleter`

Tab completion adapter for YACBA commands.

```python
class YacbaCompleter(Completer):
    def __init__(self, meta_commands: List[str])
    def get_completions(self, document, complete_event) -> Iterable[Completion]
```

**Methods**:

##### `__init__(meta_commands: List[str])`

Initialize the completer.

**Parameters**:
- `meta_commands`: List of available meta commands (e.g., `["/help", "/clear"]`)

---

##### `get_completions(document, complete_event) -> Iterable[Completion]`

Get completions for the current input.

**Parameters**:
- `document`: The current document
- `complete_event`: The completion event

**Returns**: Iterable of `Completion` objects

---

### Module: `adapters.repl_toolkit.actions.registry`

#### `YacbaActionRegistry`

Action registry that integrates YACBA-specific actions with repl-toolkit.

```python
class YacbaActionRegistry(ActionRegistry):
    def __init__(self)
```

**Registered Actions**:
- `/help` - Show available commands
- `/clear` - Clear conversation history
- `/info` - Show session information
- `/session save <name>` - Save session
- `/session load <name>` - Load session
- `/tools` - List available tools
- `/quit`, `/exit` - Exit application

**Example**:
```python
from adapters.repl_toolkit import YacbaActionRegistry

registry = YacbaActionRegistry()
commands = registry.list_commands()
print(commands)  # ['/help', '/clear', '/info', ...]
```

---

## Utilities

### Module: `utils.config_utils`

#### `discover_tool_configs(tool_configs_dir: str) -> Tuple[List[Path], ToolDiscoveryResult]`

Discover tool configuration files in a directory.

**Parameters**:
- `tool_configs_dir`: Path to directory containing tool configs

**Returns**: Tuple of:
- List of discovered tool config file paths
- `ToolDiscoveryResult` with discovery statistics

**Example**:
```python
from utils.config_utils import discover_tool_configs

tool_paths, result = discover_tool_configs("./tools")
print(f"Found {len(tool_paths)} tool configs")
print(f"Errors: {result.errors}")
```

---

### Module: `utils.file_utils`

#### `validate_file_path(path: str) -> bool`

Validate that a file path exists and is accessible.

**Parameters**:
- `path`: File path to validate

**Returns**: `True` if valid, `False` otherwise

---

#### `load_file_content(path: Path, content_type: str) -> str`

Load file content with appropriate handling for content type.

**Parameters**:
- `path`: Path to file
- `content_type`: Type of content ('text', 'json', 'yaml', etc.)

**Returns**: File content as string

**Raises**: `IOError` if file cannot be read

---

#### `resolve_glob(pattern: str) -> List[str]`

Resolve a glob pattern to list of file paths.

**Parameters**:
- `pattern`: Glob pattern (e.g., `"*.py"`, `"data/*.json"`)

**Returns**: List of matching file paths

**Example**:
```python
from utils.file_utils import resolve_glob

files = resolve_glob("*.py")
print(f"Found {len(files)} Python files")
```

---

#### `get_file_size(path: Path) -> int`

Get file size in bytes.

**Parameters**:
- `path`: Path to file

**Returns**: File size in bytes

---

### Module: `utils.model_config_parser`

#### `ModelConfigParser`

Parser for model configuration files and command-line overrides.

```python
class ModelConfigParser:
    @staticmethod
    def load_config_file(file_path: Union[str, Path]) -> Dict[str, Any]
    
    @staticmethod
    def parse_property_override(property_override: str) -> tuple[str, Any]
    
    @staticmethod
    def apply_property_override(config: Dict[str, Any], property_path: str, value: Any) -> None
    
    @staticmethod
    def merge_configs(base_config: Dict[str, Any], overrides: List[str]) -> Dict[str, Any]
    
    @staticmethod
    def validate_model_config(config: Dict[str, Any]) -> None
```

**Methods**:

##### `load_config_file(file_path: Union[str, Path]) -> Dict[str, Any]`

Load model configuration from a YAML file.

**Parameters**:
- `file_path`: Path to YAML configuration file

**Returns**: Dictionary containing the configuration

**Raises**: `ModelConfigError` if file cannot be loaded or parsed

---

##### `parse_property_override(property_override: str) -> tuple[str, Any]`

Parse a property override string in format "path:value".

**Parameters**:
- `property_override`: String in format "property.path:value"

**Returns**: Tuple of (property_path, parsed_value)

**Raises**: `ModelConfigError` if format is invalid

**Example**:
```python
from utils.model_config_parser import ModelConfigParser

path, value = ModelConfigParser.parse_property_override("temperature:0.7")
# path = "temperature", value = 0.7 (float)

path, value = ModelConfigParser.parse_property_override("response_format.type:json_object")
# path = "response_format.type", value = "json_object" (str)
```

---

##### `apply_property_override(config: Dict[str, Any], property_path: str, value: Any) -> None`

Apply a property override to a configuration dictionary using dot notation and array indexing.

**Parameters**:
- `config`: Configuration dictionary to modify
- `property_path`: Property path (e.g., "response_format.type" or "safety_settings[0].category")
- `value`: Value to set

**Raises**: `ModelConfigError` if property path is invalid

**Example**:
```python
config = {}
ModelConfigParser.apply_property_override(config, "temperature", 0.7)
# config = {"temperature": 0.7}

ModelConfigParser.apply_property_override(config, "response_format.type", "json_object")
# config = {"temperature": 0.7, "response_format": {"type": "json_object"}}
```

---

##### `merge_configs(base_config: Dict[str, Any], overrides: List[str]) -> Dict[str, Any]`

Merge a base configuration with a list of property overrides.

**Parameters**:
- `base_config`: Base configuration dictionary
- `overrides`: List of property override strings

**Returns**: Merged configuration dictionary

**Raises**: `ModelConfigError` if any override is invalid

**Example**:
```python
base = {"temperature": 0.5, "max_tokens": 1000}
overrides = ["temperature:0.7", "top_p:0.9"]
merged = ModelConfigParser.merge_configs(base, overrides)
# merged = {"temperature": 0.7, "max_tokens": 1000, "top_p": 0.9}
```

---

#### `parse_model_config(config_file: Optional[str], overrides: Optional[List[str]]) -> Dict[str, Any]`

Parse model configuration from file and/or command-line overrides.

**Parameters**:
- `config_file`: Optional path to YAML configuration file
- `overrides`: Optional list of property override strings

**Returns**: Parsed and merged configuration dictionary

**Raises**: `ModelConfigError` if configuration is invalid

**Example**:
```python
from utils.model_config_parser import parse_model_config

# From file only
config = parse_model_config("model_config.yaml", None)

# From overrides only
config = parse_model_config(None, ["temperature:0.7", "max_tokens:2000"])

# From both (overrides take precedence)
config = parse_model_config("model_config.yaml", ["temperature:0.7"])
```

---

### Module: `utils.startup_messages`

#### `print_startup_info(...)`

Print startup information to console.

**Parameters**:
- `model_id: str` - Model identifier
- `system_prompt: str` - System prompt text
- `prompt_source: str` - Source of system prompt
- `tools: List` - List of available tools
- `startup_files: List` - List of startup files
- `conversation_manager_info: str` - Conversation manager info

**Example**:
```python
from utils.startup_messages import print_startup_info

print_startup_info(
    model_id="gpt-4o",
    system_prompt="You are a helpful assistant",
    prompt_source="cli",
    tools=[],
    startup_files=[],
    conversation_manager_info="Conversation Manager: sliding_window"
)
```

---

#### `print_welcome_message()`

Print welcome message to console.

**Example**:
```python
from utils.startup_messages import print_welcome_message

print_welcome_message()
# Prints:
# Welcome to Yet Another ChatBot Agent!
# Type 'exit' or 'quit' to end. Type /help for a list of commands.
# ...
```

---

## Type Definitions

### Module: `yacba_types.base`

#### `PathLike`

Type alias for path-like objects.

```python
PathLike = Union[str, Path]
```

---

#### `ExitCode`

Enum for exit codes.

```python
class ExitCode(IntEnum):
    SUCCESS = 0
    USER_INTERRUPT = 1
    CONFIG_ERROR = 2
    RUNTIME_ERROR = 3
    FATAL_ERROR = 4
```

---

### Module: `yacba_types.config`

#### `FileUpload`

Type alias for file upload specifications.

```python
FileUpload = Union[
    Tuple[str, str],           # (path, mimetype)
    Tuple[str, Optional[str]], # (path, optional mimetype)
    Dict[str, Any]             # {"path": str, "mimetype": str}
]
```

---

#### `ToolDiscoveryResult`

Dataclass for tool discovery results.

```python
@dataclass
class ToolDiscoveryResult:
    discovered_count: int
    loaded_count: int
    errors: List[str]
```

---

### Module: `yacba_types.content`

#### `Message`

Type alias for message content.

```python
Message = Dict[str, Any]
```

---

## Main Entry Point

### Module: `yacba`

#### `main() -> NoReturn`

Synchronous main entry point. Configures logging and runs the async application.

**Raises**: `SystemExit` with appropriate exit code

**Example**:
```python
if __name__ == "__main__":
    main()
```

---

#### `async _run_agent_lifecycle(config: YacbaConfig) -> None`

Main agent lifecycle: configure, create agent, and run interface.

**Parameters**:
- `config`: Validated YACBA configuration

**Raises**: `Exception` on any error during agent lifecycle

---

#### `async _run_interactive_mode(agent: AgentProxy, action_registry: YacbaActionRegistry, config: YacbaConfig) -> None`

Run in interactive mode using repl_toolkit.

**Parameters**:
- `agent`: The agent proxy
- `action_registry`: The action registry
- `config`: YACBA configuration

---

#### `async _run_headless_mode(agent: AgentProxy, action_registry: YacbaActionRegistry, config: YacbaConfig) -> None`

Run in headless mode using repl_toolkit.

**Parameters**:
- `agent`: The agent proxy
- `action_registry`: The action registry
- `config`: YACBA configuration

---

## Error Handling

### Exception Hierarchy

```
Exception
├── ModelConfigError (utils.model_config_parser)
│   └── Raised for model configuration parsing errors
├── ConfigurationError (strands_agent_factory)
│   └── Raised for invalid configuration
└── SystemExit (built-in)
    └── Used for clean exits with exit codes
```

### Exit Codes

- `0` - Success
- `1` - User interrupt (Ctrl+C)
- `2` - Configuration error
- `3` - Runtime error
- `4` - Fatal error

---

## Usage Examples

### Basic Usage

```python
from config import parse_config
from adapters.strands_factory import YacbaToStrandsConfigConverter
from strands_agent_factory import AgentFactory

# Parse configuration
config = parse_config()

# Convert to strands format
converter = YacbaToStrandsConfigConverter(config)
strands_config = converter.convert()

# Create agent
factory = AgentFactory(config=strands_config)
await factory.initialize()
agent = factory.create_agent()

# Use agent
with agent as agent_context:
    await agent_context.send_message_to_agent("Hello!")
```

---

### Custom Configuration

```python
from config.dataclass import YacbaConfig

config = YacbaConfig(
    model_string="gpt-4o",
    system_prompt="You are a helpful assistant",
    prompt_source="api",
    tool_config_paths=[],
    startup_files_content=None,
    conversation_manager_type="sliding_window",
    sliding_window_size=50,
    show_tool_use=True
)
```

---

### Model Configuration

```python
from utils.model_config_parser import parse_model_config

# From file
config = parse_model_config("model_config.yaml", None)

# From CLI overrides
config = parse_model_config(None, [
    "temperature:0.7",
    "max_tokens:2000",
    "response_format.type:json_object"
])

# Combined
config = parse_model_config("model_config.yaml", ["temperature:0.8"])
```

---

## Best Practices

### Configuration

1. **Use profiles** for different environments (dev, prod, research)
2. **Validate early** - use `--show-config` to verify configuration
3. **Use environment variables** for sensitive data (API keys)
4. **Document custom prompts** in separate files with `@file.txt` syntax

### Error Handling

1. **Check return values** from async functions
2. **Use try-except** around agent operations
3. **Log errors** with appropriate log levels
4. **Provide context** in error messages

### Performance

1. **Use sliding window** for long conversations
2. **Choose appropriate models** (cheaper for summarization)
3. **Limit file uploads** with `--max-files`
4. **Enable truncation** for large tool results

---

## See Also

- [Architecture Documentation](ARCHITECTURE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Configuration Guide](../README.CONFIG.md)
- [Model Configuration Guide](../README.MODEL_CONFIG.md)
