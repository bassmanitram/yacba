# YACBA - Yet Another ChatBot Agent

**Refactored Architecture (v2.0)** - A chatbot framework built on specialized packages for modularity and maintainability.

## Architecture Overview

YACBA has been refactored to leverage specialized packages:

- **YACBA Core**: Configuration management, CLI parsing, and orchestration
- **[strands_agent_factory](https://github.com/bassmanitram/strands-agent-factory)**: Agent lifecycle, tool management, and AI provider integration
- **[repl_toolkit](https://github.com/your-org/repl-toolkit)**: Interactive and headless user interfaces with prompt_toolkit

This separation of concerns provides:
- Better maintainability: Each package handles its domain
- Leverage specialized functionality from each package
- Clean interfaces between components
- Easy to upgrade individual components

## Quick Start

### Installation


> **⚠️ Important**: `strands-agent-factory` is **not available on PyPI** and must be installed from GitHub due to copyright considerations. The `requirements.txt` file already includes the correct GitHub installation URL. See [README_INSTALLATION_NOTE.md](README_INSTALLATION_NOTE.md) for details.

```bash
# Clone the repository
git clone https://github.com/your-username/yacba.git
cd yacba/code

# Install dependencies (including strands_agent_factory and repl_toolkit)
pip install -r requirements.txt

# Basic usage
python yacba.py --help
```

### Basic Examples

```bash
# Interactive mode (default)
python yacba.py --model "gpt-4o"

# Headless mode for scripting  
python yacba.py --headless --initial-message "Analyze the current directory"

# With tools and files
python yacba.py --tool-configs-dir ./tools --files "*.py" "text/plain"

# Custom conversation management
python yacba.py --conversation-manager sliding_window --window-size 50
```

## Key Features

### AI Provider Support
- OpenAI: GPT-4, GPT-4o, GPT-3.5 models
- Anthropic: Claude 3.5 Sonnet, Claude 3 Opus/Haiku  
- Google: Gemini 2.5 Flash, Gemini Pro via LiteLLM
- Local Models: Ollama integration
- AWS Bedrock: Enterprise deployment
- 100+ Providers: Via LiteLLM integration

### Tool System
- Python Functions: Load any Python function as a tool
- MCP Servers: Model Context Protocol server integration
- Automatic Discovery: Scan directories for tool configurations
- Dynamic Loading: Hot-reload tools without restart
- Schema Adaptation: Automatic tool schema conversion for different AI providers

### Conversation Management
- Sliding Window: Keep recent messages, forget old ones
- Summarizing: AI-powered summarization of conversation history
- Null Manager: Disable management for unlimited context
- Configurable Thresholds: Fine-tune memory management

### Interactive Experience
- Prompt Toolkit: Full-featured readline with history, completion
- Command System: Built-in commands for session management
- Cancellation Support: Cancel long-running operations with Alt+C
- Multi-line Input: Alt+Enter to send, Enter for new line
- Intelligent Tab Completion:
  - **Command Completion**: `/he<Tab>` → `/help` (alphabetically sorted)
  - **File Path Completion**: `file("/tmp/<Tab>` → complete paths in `file()` syntax
  - **Shell Variable Expansion**: `${HOME}<Tab>` → `/home/user` (expands environment variables)
  - **Shell Command Expansion**: `$(whoami)<Tab>` → `username` (executes and expands shell commands)

### Session Persistence
- Named Sessions: Resume conversations by name
- File-based Storage: Persistent conversation history
- Agent Identity: Custom agent IDs for multi-agent workflows
- History Management: Configurable history retention

### File Processing
- Multi-modal Support: PDF, DOC, CSV, JSON, Markdown, images
- Batch Upload: Upload multiple files simultaneously  
- Content Extraction: Automatic content parsing and preparation
- Mimetype Detection: Automatic or manual mimetype specification

## Command Line Interface

YACBA provides a CLI with over 20 options for customization:

### Core Configuration
```bash
python yacba.py [OPTIONS]

Required:
  -m, --model MODEL                AI model in <framework>:<model> format
                                  Examples: "gpt-4o", "anthropic:claude-3-5-sonnet", 
                                           "litellm:gemini/gemini-2.5-flash"

System Behavior:
  -s, --system-prompt PROMPT      Custom system prompt for the agent
  --emulate-system-prompt         Use user message format for unsupported models
  -H, --headless                  Non-interactive mode for scripting
  -i, --initial-message MSG       Message to send on startup

Tool Integration:
  -t, --tool-configs-dir DIR      Directory containing tool configuration files
  -f, --files GLOB [MIMETYPE]     Files to upload (repeatable)
  --max-files N                   Maximum files to process (default: 10)

Model Configuration:
  --model-config FILE             JSON file with model parameters
  -c, --config-override KEY:VAL   Override specific config values (repeatable)
  --summarization-model-config FILE  JSON file with summarization model parameters
  -C, --summarization-config-override KEY:VAL  Override summarization model config (repeatable)

Session Management:
  --session NAME                  Named session for persistence
  --agent-id ID                   Custom agent identifier

Conversation Management:
  --conversation-manager TYPE     Strategy: null, sliding_window, summarizing
  --window-size N                 Messages in sliding window (default: 40)
  --preserve-recent N             Always keep recent N messages (default: 10)
  --summary-ratio RATIO           Summarization ratio 0.1-0.8 (default: 0.3)
  --summarization-model MODEL     Separate model for summaries
  --custom-summarization-prompt   Custom summarization prompt
  --no-truncate-results           Disable tool result truncation

User Interface:
  --cli-prompt PROMPT             Custom input prompt with HTML formatting
  --response-prefix PREFIX        Custom response prefix with HTML formatting  
  --show-tool-use                 Show detailed tool execution info

Configuration Management:
  --profile PROFILE               Use named configuration profile
  --config-file FILE              Configuration file path
  --list-profiles                 Show available profiles
  --show-config                   Display resolved configuration
  --init-config PATH              Create sample configuration file
```

### Configuration File Support

Create reusable configuration profiles:

```yaml
# ~/.yacba/config.yaml
profiles:
  development:
    model: "litellm:gemini/gemini-2.5-flash"
    tool_configs_dir: "./dev-tools"
    conversation_manager: "sliding_window"
    window_size: 30
    show_tool_use: true
    
  production:
    model: "anthropic:claude-3-5-sonnet"
    conversation_manager: "summarizing"
    preserve_recent: 15
    summary_ratio: 0.2
    
  research:
    model: "gpt-4o"
    tool_configs_dir: "./research-tools"
    max_files: 50
    conversation_manager: "null"  # Unlimited context
```

Usage: `python yacba.py --profile development`

## Tool Configuration

YACBA supports flexible tool configuration through JSON/YAML files:

### Python Function Tools
```json
{
  "tools": [
    {
      "type": "python_function",
      "module": "my_tools.calculator",
      "config": {
        "functions": ["add", "multiply", "divide"],
        "package_path": "src/",
        "base_path": "/project/root"
      }
    }
  ]
}
```

### MCP Server Tools
```json
{
  "tools": [
    {
      "type": "mcp_server", 
      "config": {
        "command": ["python", "-m", "my_mcp_server"],
        "args": ["--port", "8080"],
        "env": {"API_KEY": "${SECRET_KEY}"},
        "functions": ["search", "analyze"]
      }
    }
  ]
}
```

### Tool Discovery
Place tool configurations in any directory and point YACBA to it:

```bash
python yacba.py --tool-configs-dir ./tools/
```

YACBA will automatically discover and load all `*.json` and `*.yaml` files in the directory.

## Interactive Mode Features

### Tab Completion

YACBA provides intelligent, context-aware tab completion:

#### 1. Command Completion
Commands are alphabetically sorted for easy discovery:
```
User: /he<Tab>
→ /help

User: /co<Tab>
→ /clear
  /conversation-manager
  /conversation-stats
```

#### 2. File Path Completion
Autocomplete paths within `file()` function calls:
```
User: file("/etc/pas<Tab>
→ file("/etc/passwd
  file("/etc/password

User: file("~/Doc<Tab>
→ file("~/Documents/
```

#### 3. Shell Variable Expansion (NEW!)
Expand environment variables on Tab:
```
User: My home is ${HOME}<Tab>
→ My home is /home/username

User: Config at ${XDG_CONFIG_HOME}<Tab>
→ Config at /home/username/.config
```

#### 4. Shell Command Expansion (NEW!)
Execute and expand shell commands on Tab:
```
User: Current user is $(whoami)<Tab>
→ Current user is jbartle9

User: Today: $(date)<Tab>
→ Today: Mon Jan  6 15:23:45 PST 2025
```

**Notes**:
- Shell expansions execute with 2-second timeout
- Multi-line command output shows individual lines as options
- Maximum 30 lines displayed in completion menu
- Expansions are **on-demand** (only when Tab is pressed)

### User Interface Customization
```bash
# Custom prompts with HTML formatting
python yacba.py \
  --cli-prompt "<b><blue>User:</blue></b> " \
  --response-prefix "<b><green>Assistant:</green></b> "

# Tool usage visibility
python yacba.py --show-tool-use
```

### Built-in Commands
In interactive mode, use these commands (tab completion available, alphabetically sorted):

- `/clear` - Clear conversation history
- `/conversation-manager` - Change conversation management strategy
- `/conversation-stats` - Show conversation statistics
- `/exit` - Exit the application
- `/help` - Show available commands
- `/history` - Show conversation history
- `/info` - Show current session information (alias for `/status`)
- `/quit` - Exit the application
- `/session` - Session management (save, load, list)
- `/shell` - Execute shell commands
- `/shortcuts` - Show keyboard shortcuts
- `/stats` - Show current session information (alias for `/status`)
- `/status` - Show comprehensive session status
- `/tools` - List available tools

## Architecture Details

### Component Interaction Flow

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   YACBA Core    │────│ strands_agent_factory │────│   repl_toolkit  │
│                 │    │                      │    │                 │
│ • CLI Parsing   │    │ • Agent Lifecycle    │    │ • Interactive   │
│ • Config Mgmt   │────│ • Tool Management    │────│ • Headless      │  
│ • File Proc     │    │ • AI Integration     │    │ • Commands      │
│ • Orchestration │    │ • Session Persist   │    │ • Completion    │
└─────────────────┘    └──────────────────────┘    └─────────────────┘
         │                        │                         │
         ▼                        ▼                         ▼
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│ YacbaConfig     │    │   AgentFactory       │    │  AsyncREPL      │
└─────────────────┘    └──────────────────────┘    └─────────────────┘
```

### Adapter Pattern Implementation

The refactored architecture uses adapters to bridge between packages:

1. **YacbaToStrandsConfigConverter**: Converts YACBA configuration to strands_agent_factory format
2. **YacbaBackend**: Implements repl_toolkit protocols using strands_agent_factory agents
3. **YacbaActionRegistry**: Registers YACBA-specific commands with repl_toolkit
4. **Completion System**: Modular completers for different contexts
   - **PrefixCompleter**: Alphabetically sorted `/` commands from repl_toolkit
   - **ShellExpansionCompleter**: `${VAR}` and `$(cmd)` expansion from repl_toolkit
   - **YacbaCompleter**: `file()` path completion (YACBA-specific)

## Performance & Scalability

### Memory Management
- Conversation Strategies: Automatic context window management
- Tool Result Caching: Caching of expensive tool operations
- Session Persistence: Efficient storage of conversation state

### Best Practices
- Use sliding window for long conversations
- Choose appropriate models for different tasks
- Configure session persistence for multi-turn workflows
- Use MCP servers for external system integration

## Debugging & Troubleshooting

### Logging Configuration
```bash
# Enable debug logging
export LOGURU_LEVEL=DEBUG
python yacba.py --model "gpt-4o"

# Enable trace-level for detailed debugging  
export LOGURU_LEVEL=TRACE
python yacba.py --show-config
```

### Common Issues

1. **Module Import Errors**: Ensure strands_agent_factory and repl_toolkit are in Python path
2. **API Credentials**: Set appropriate environment variables (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
3. **Tool Loading Failures**: Check tool configuration syntax and file paths
4. **Memory Issues**: Adjust conversation manager settings for large contexts

### Configuration Validation
```bash
# Validate configuration without starting agent
python yacba.py --show-config

# Test specific profile
python yacba.py --profile development --show-config

# Initialize sample configuration
python yacba.py --init-config ~/.yacba/sample-config.yaml
```

## Migration from Legacy YACBA

The refactored YACBA maintains backward compatibility:

### Command Line Arguments
- All existing arguments preserved
- Same behavior and semantics
- Configuration files unchanged

### Breaking Changes
- None - Complete backward compatibility maintained

### Migration Steps
1. Update dependencies: `pip install -r requirements.txt`
2. Replace `python yacba.py` with `python yacba.py`
3. All existing scripts and configurations continue to work unchanged

## Future Roadmap

- Plugin System: Dynamic plugin loading for custom adapters
- Web Interface: Browser-based interface option
- Multi-Agent Orchestration: Coordinate multiple AI agents
- Tool Authoring: Visual tool creation interface
- Cloud Deployment: Containerized deployment options
- Performance Analytics: Usage and performance metrics

## Contributing

Contributions are welcome. The modular architecture makes it easy to contribute to specific areas:

1. **YACBA Core**: Configuration, CLI improvements, file processing
2. **Tool Integrations**: New tool types, MCP server implementations
3. **UI Enhancements**: Interactive features, command improvements
4. **Documentation**: Examples, tutorials, best practices

### Development Setup
```bash
git clone https://github.com/your-username/yacba.git
cd yacba/code

# Install in development mode
pip install -e .

# Run tests
python test_refactored_yacba.py
```

### Architecture Guidelines
- Separation of Concerns: Each package handles its domain
- Protocol-Based Design: Use protocols for loose coupling
- Backward Compatibility: Never break existing functionality
- Testing: All changes must include tests

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [strands-agents](https://github.com/pydantic/strands-agents): Core AI agent framework
- [strands_agent_factory](https://github.com/bassmanitram/strands-agent-factory): Agent lifecycle management
- [repl_toolkit](https://github.com/your-org/repl-toolkit): Interactive interface framework
- [prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit): Terminal interfaces
- All contributors

## Documentation

For detailed documentation, see the [docs/](docs/) directory:

- [API Documentation](docs/API.md) - Complete API reference
- [Architecture Documentation](docs/ARCHITECTURE.md) - System design and architecture
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md) - Problem solving and debugging
- [Configuration Guide](README.CONFIG.md) - Configuration system details
- [Model Configuration Guide](README.MODEL_CONFIG.md) - Model config parsing
