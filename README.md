# YACBA - CLI Interface for strands-agent-factory

**Command-line interface and configuration management for AI agents**

> **Built on [strands-agent-factory](https://github.com/JBarmentlo/strands-agent-factory)**, which itself is built on [strands-agents](https://github.com/pydantic/strands-agents).
>
>  **For core AI agent concepts, tool development, and advanced features**, refer to the [strands-agent-factory documentation](https://github.com/JBarmentlo/strands-agent-factory#readme).

---

## What is YACBA?

YACBA provides a **command-line interface** and **configuration management layer** on top of strands-agent-factory. It's designed for users who want quick access to AI agents through the terminal, with features like:

- **CLI Interface**: Full-featured command-line argument parsing (via [dataclass-args](https://pypi.org/project/dataclass-args/))
- **Profile System**: Reusable YAML/JSON configuration profiles (via [profile-config](https://pypi.org/project/profile-config/))
- **Interactive Mode**: REPL with tab completion, history, and commands (via [repl-toolkit](https://pypi.org/project/repl-toolkit/))
- **Headless Mode**: Script-friendly automation for CI/CD pipelines
- **File Management**: Glob patterns, MIME detection, bulk upload

**Core agent functionality** (LLM integration, tool execution, conversation management, A2A support) comes from [strands-agent-factory](https://github.com/JBarmentlo/strands-agent-factory).

---

## When to Use YACBA vs strands-agent-factory Directly

### Use YACBA when you want:
-  Command-line interface for quick agent interactions
-  Configuration profiles for different contexts (dev, prod, research)
-  Interactive chat sessions with history and tab completion
-  Scriptable headless mode for automation

### Use strands-agent-factory directly when you want:
-  To embed agents in Python applications
-  Full programmatic control over agent behavior
-  Custom UI/UX beyond terminal interfaces
-  Advanced customization beyond YACBA's scope

---

## Quick Start

### Installation

> **⚠️ Important**: `strands-agent-factory` is installed from GitHub (not PyPI). The requirements file handles this automatically.

```bash
# Clone the repository
git clone https://github.com/your-username/yacba.git
cd yacba/code

# Install dependencies
pip install -r requirements.txt

# Run YACBA
python yacba.py --help
```

### Basic Usage

```bash
# Interactive mode
python yacba.py -m "gpt-4o"

# With tools
python yacba.py -m "gpt-4o" -t ./sample-tool-configs

# Headless mode (for scripts)
python yacba.py -m "gpt-4o" -H -i "Analyze the current directory"

# With configuration profile
python yacba.py --profile development
```

### First Conversation

```bash
# Start an interactive session
python yacba.py -m "anthropic:claude-3-5-sonnet-20241022" -s "You are a helpful coding assistant"

# In the REPL:
User: /help                    # List available commands
User: What is Python?          # Chat with the agent
User: file("script.py")        # Upload a file mid-conversation
User: /status                  # Check session status
User: /exit                    # Exit
```

---

## Features

### What YACBA Adds

These features are provided by YACBA on top of strands-agent-factory:

#### CLI Interface (dataclass-args)
- Auto-generated argument parser from configuration dataclass
- File loading with `@file.txt` syntax for many arguments
- Property overrides with `--mc` and `--smc` for model configs
- See [CLI Reference](#cli-reference) below

#### Profile System (profile-config)
- YAML/JSON configuration files
- Profile inheritance and composition
- Environment variable substitution
- Configuration discovery in standard locations

#### Interactive Mode (repl-toolkit)
- Full-featured REPL with prompt_toolkit
- Tab completion for:
  - Commands: `/help<Tab>` → `/help`
  - File paths: `file("/tmp/<Tab>` → completions
  - Shell variables: `${HOME}<Tab>` → `/home/user`
  - Shell commands: `$(whoami)<Tab>` → `username`
- Command history with search
- Multi-line input (Alt+Enter)
- Cancellation support (Alt+C)

#### Headless Mode
- Non-interactive automation
- Exit after initial message
- Script-friendly output
- CI/CD integration

### What strands-agent-factory Provides

These core features come from [strands-agent-factory](https://github.com/JBarmentlo/strands-agent-factory):

- **LLM Integration**: OpenAI, Anthropic, Google, AWS Bedrock, 100+ providers via LiteLLM
- **Tool System**: Python functions, MCP servers, A2A (Agent-to-Agent) tools
- **Conversation Management**: Sliding window, summarization strategies
- **Session Persistence**: Save/restore conversation state
- **Tool Execution**: Parallel execution, error handling, result formatting

 **See [strands-agent-factory documentation](https://github.com/JBarmentlo/strands-agent-factory#readme) for details on these features.**

---

## Tool Configuration

YACBA uses [strands-agent-factory's tool system](https://github.com/JBarmentlo/strands-agent-factory#tools). Tool configurations are JSON files that define what tools your agent can use.

### Tool Types

All tool types below are provided by strands-agent-factory:

#### 1. Python Function Tools

Load Python functions as tools:

```json
{
  "id": "strands-tools",
  "type": "python",
  "module_path": "strands_tools",
  "functions": ["shell", "file_read", "file_write"]
}
```

 See: [`sample-tool-configs/strands.tools.json`](./sample-tool-configs/strands.tools.json)

#### 2. MCP Server Tools

Connect to [Model Context Protocol](https://modelcontextprotocol.io/) servers:

```json
{
  "id": "aws-cli-mcp",
  "type": "mcp",
  "command": "uvx",
  "args": ["-q", "awslabs.aws-api-mcp-server@latest"],
  "env": {
    "FASTMCP_LOG_LEVEL": "ERROR"
  }
}
```

 See: [`sample-tool-configs/aws-cli.tools.json`](./sample-tool-configs/aws-cli.tools.json)

#### 3. A2A (Agent-to-Agent) Tools

Connect to other AI agents as tools:

```json
{
  "id": "research-agents",
  "type": "a2a",
  "urls": [
    "https://research-agent-1.example.com",
    "https://research-agent-2.example.com"
  ],
  "timeout": 300
}
```

 See: [`sample-tool-configs/a2a-example.tools.json`](./sample-tool-configs/a2a-example.tools.json)

 **For tool development and A2A setup**, see [strands-agent-factory tool documentation](https://github.com/JBarmentlo/strands-agent-factory#tools).

### Using Tools

```bash
# Specify tool configuration directory
python yacba.py -m "gpt-4o" -t ./sample-tool-configs

# Agent will have access to all tools defined in that directory
```

---

## CLI Reference

YACBA's CLI is auto-generated from the `YacbaConfig` dataclass via [dataclass-args](https://pypi.org/project/dataclass-args/).

### Full Help

```bash
python yacba.py --help
```

### Key Options

```
usage: yacba.py [-h] [--profile PROFILE] [--config-file CONFIG_FILE] 
                [-m MODEL_STRING] [-s SYSTEM_PROMPT] [-t TOOL_CONFIGS_DIR]
                [-f FILE_GLOB [MIMETYPE ...]] [-H] [-i INITIAL_MESSAGE]
                [many more options...]

Required:
  -m, --model-string MODEL_STRING
                        Model to use (format: framework:model_name)
                        Examples: "gpt-4o", "anthropic:claude-3-5-sonnet-20241022",
                                  "litellm:gemini/gemini-2.5-flash"

Common Options:
  -s, --system-prompt SYSTEM_PROMPT
                        System prompt (supports @file.txt to load from file)
  -t, --tool-configs-dir TOOL_CONFIGS_DIR
                        Directory containing tool configuration files
  -f, --files FILE_GLOB [MIMETYPE ...]
                        File(s) to upload at startup (repeatable)
  -H, --headless        Run in non-interactive mode
  -i, --initial-message INITIAL_MESSAGE
                        Message to send on startup (supports @file.txt)

Profile Management:
  --profile PROFILE     Use named configuration profile
  --config-file CONFIG_FILE
                        Path to configuration file
  --list-profiles       List available profiles
  --show-config         Display resolved configuration

Model Configuration:
  --model-config MODEL_CONFIG
                        Model config JSON file
  --mc MC               Model config property override (key.path:value)
  --summarization-model SUMMARIZATION_MODEL
                        Separate model for summarization
  --summarization-model-config SUMMARIZATION_MODEL_CONFIG
                        Summarization model config file
  --smc SMC             Summarization config override (key.path:value)

Conversation Management:
  --conversation-manager-type {null,sliding_window,summarizing}
                        Strategy: null, sliding_window, or summarizing
  --sliding-window-size SLIDING_WINDOW_SIZE
                        Number of messages to keep
  --preserve-recent-messages PRESERVE_RECENT_MESSAGES
                        Messages to always preserve when summarizing
  --summary-ratio SUMMARY_RATIO
                        Summary length ratio (0.0-1.0)

Session Management:
  --session-name SESSION_NAME
                        Named session for persistence
  --agent-id AGENT_ID   Agent identifier

UI Customization:
  --cli-prompt CLI_PROMPT
                        Custom prompt string (supports @file.txt)
  --response-prefix RESPONSE_PREFIX
                        Custom response prefix (supports @file.txt)
  --show-tool-use       Display tool execution details
```

For complete option list: `python yacba.py --help`

---

## Configuration System

### Configuration Files

YACBA uses [profile-config](https://pypi.org/project/profile-config/) for configuration management.

```yaml
# ~/.yacba/config.yaml
profiles:
  development:
    model_string: "litellm:gemini/gemini-2.5-flash"
    tool_configs_dir: "./dev-tools"
    conversation_manager_type: "sliding_window"
    sliding_window_size: 30
    show_tool_use: true
    
  production:
    model_string: "anthropic:claude-3-5-sonnet-20241022"
    conversation_manager_type: "summarizing"
    preserve_recent_messages: 15
    summary_ratio: 0.2
    
  research:
    model_string: "gpt-4o"
    tool_configs_dir: "./research-tools"
    max_files: 50
    conversation_manager_type: "null"  # Unlimited context
```

### Configuration Precedence

1. **CLI arguments** (highest priority)
2. **User-specified config file** (`--config-file`)
3. **Discovered config files** (`~/.yacba/config.yaml`, `./yacba.yaml`)
4. **Environment variables**
5. **Default values** (lowest priority)

### Using Profiles

```bash
# Use a profile
python yacba.py --profile development

# Override profile settings
python yacba.py --profile development -m "gpt-4o" --show-tool-use

# Create sample config
python yacba.py --init-config ~/.yacba/config.yaml
```

---

## Interactive Mode Commands

When running in interactive mode, use these built-in commands:

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/shortcuts` | Show keyboard shortcuts |
| `/status` | Show comprehensive session status |
| `/info` | Alias for `/status` |
| `/stats` | Alias for `/status` |
| `/tools` | List available tools |
| `/history` | Show conversation history |
| `/clear` | Clear conversation history |
| `/session save [name]` | Save current session |
| `/session load <name>` | Load saved session |
| `/session list` | List saved sessions |
| `/conversation-manager [type]` | Change conversation manager |
| `/conversation-stats` | Show conversation statistics |
| `/shell <command>` | Execute shell command |
| `/exit` | Exit the application |
| `/quit` | Exit the application |

Commands have tab completion (sorted alphabetically).

---

## Advanced Features

### Tab Completion

YACBA provides intelligent, context-aware tab completion:

1. **Commands**: `/he<Tab>` → `/help`
2. **File paths**: `file("/tmp/<Tab>` → directory contents
3. **Shell variables**: `${HOME}<Tab>` → `/home/user`
4. **Shell commands**: `$(whoami)<Tab>` → `username`

### File Loading Syntax

Many arguments support loading from files:

```bash
# Load system prompt from file
python yacba.py -m "gpt-4o" -s @prompts/coding-assistant.txt

# Load initial message from file
python yacba.py -m "gpt-4o" -H -i @queries/analysis-request.txt
```

### Model Configuration Files

Fine-tune model parameters:

```json
{
  "temperature": 0.7,
  "max_tokens": 2000,
  "top_p": 0.9,
  "frequency_penalty": 0.0
}
```

```bash
python yacba.py -m "gpt-4o" --model-config ./sample-model-configs/openai-gpt4.json
```

 See: [`sample-model-configs/`](./sample-model-configs/) for examples

### Property Overrides

Override specific config properties:

```bash
# Override model temperature
python yacba.py -m "gpt-4o" --model-config config.json --mc temperature:0.9

# Multiple overrides
python yacba.py -m "gpt-4o" --mc temperature:0.7 --mc max_tokens:1000
```

---

## Examples

### Basic Chat

```bash
python yacba.py -m "gpt-4o" -s "You are a helpful assistant"
```

### With Tools

```bash
python yacba.py -m "gpt-4o" -t ./sample-tool-configs -s "You are a system administrator assistant"
```

### Headless Automation

```bash
python yacba.py -m "gpt-4o" -H -i "Summarize all Python files in the current directory" \
  -t ./sample-tool-configs -f "*.py" "text/plain"
```

### With Configuration Profile

```bash
python yacba.py --profile development
```

### A2A Multi-Agent Setup

```bash
# Main agent with access to specialized agents as tools
python yacba.py -m "gpt-4o" -t ./a2a-tools \
  -s "You are a project manager who coordinates with specialized agents"
```

(Requires A2A agents running at the URLs specified in `./a2a-tools/`)

---

## Architecture

YACBA sits atop strands-agent-factory, providing CLI/configuration convenience:

```
┌──────────────────────────────────────────────────────┐
│                  strands-agents                      │
│            (Core AI Agent Framework)                 │
└────────────────────┬─────────────────────────────────┘
                     │
                     │ builds on
                     ▼
┌──────────────────────────────────────────────────────┐
│            strands-agent-factory                     │
│  • Agent lifecycle   • Tool management               │
│  • Conversation mgmt • Provider adapters             │
│  • Session storage   • A2A support                   │
└────────────────────┬─────────────────────────────────┘
                     │
                     │ wrapped by
                     ▼
┌──────────────────────────────────────────────────────┐
│                    YACBA                             │
│  • CLI interface  • Profile system                   │
│  • Interactive    • Configuration                    │
│  • Headless mode  • File management                  │
└──────────────────────────────────────────────────────┘
```

### YACBA's Role

YACBA is a **thin wrapper** that:
1. Parses CLI arguments (dataclass-args)
2. Loads configuration profiles (profile-config)
3. Converts to strands-agent-factory config format
4. Creates and runs agents via strands-agent-factory
5. Provides REPL interface (repl-toolkit)

**All core agent functionality** comes from strands-agent-factory.

---

## Troubleshooting

### Common Issues

**Module Import Errors**
```bash
# Ensure dependencies are installed
pip install -r requirements.txt
```

**API Credentials**
```bash
# Set appropriate environment variables
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

**Tool Loading Failures**
- Check tool configuration syntax matches strands-agent-factory format
- Verify file paths in tool configs
- See [strands-agent-factory tool docs](https://github.com/JBarmentlo/strands-agent-factory#tools)

### Debug Logging

```bash
# Enable debug logging
export LOGURU_LEVEL=DEBUG
python yacba.py -m "gpt-4o"

# Trace level (very verbose)
export LOGURU_LEVEL=TRACE
python yacba.py --show-config
```

### Validate Configuration

```bash
# Show resolved configuration
python yacba.py --profile development --show-config

# List available profiles
python yacba.py --list-profiles
```

---

## Documentation

- **YACBA Docs**: See [`docs/`](./docs/) directory
  - [API Reference](docs/API.md) - YACBA's wrapper APIs
  - [Architecture](docs/ARCHITECTURE.md) - System design
  - [Troubleshooting](docs/TROUBLESHOOTING.md) - Problem solving
  - [Completion System](docs/COMPLETION_SYSTEM.md) - Tab completion details

-  **strands-agent-factory Docs**: [GitHub Repository](https://github.com/JBarmentlo/strands-agent-factory#readme)
  - Core agent concepts
  - Tool development guide
  - A2A setup instructions
  - Provider configuration
  - Conversation management strategies

-  **strands-agents Docs**: [GitHub Repository](https://github.com/pydantic/strands-agents)
  - Underlying agent framework
  - Advanced customization

---

## Contributing

Contributions welcome! YACBA's modular architecture makes it easy to contribute:

- **YACBA Layer**: CLI, configuration, REPL enhancements
- **strands-agent-factory**: Core agent features, tools (contribute there)
- **Documentation**: Examples, tutorials, guides

### Development Setup

```bash
git clone https://github.com/your-username/yacba.git
cd yacba/code

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/
```

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **[strands-agents](https://github.com/pydantic/strands-agents)**: Foundation AI agent framework
- **[strands-agent-factory](https://github.com/JBarmentlo/strands-agent-factory)**: Agent lifecycle and tool management
- **[repl-toolkit](https://pypi.org/project/repl-toolkit/)**: Interactive REPL framework
- **[dataclass-args](https://pypi.org/project/dataclass-args/)**: CLI argument parsing
- **[profile-config](https://pypi.org/project/profile-config/)**: Configuration management
- **[prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit)**: Terminal UI components

---

## Related Projects

- **[strands-agent-factory](https://github.com/JBarmentlo/strands-agent-factory)** - Core agent factory this wraps
- **[strands-agents](https://github.com/pydantic/strands-agents)** - Underlying agent framework
- **[repl-toolkit](https://github.com/your-org/repl-toolkit)** - REPL framework used here

---

**Questions? Issues?**

- YACBA Issues: [GitHub Issues](https://github.com/your-username/yacba/issues)
- strands-agent-factory Issues: [GitHub Issues](https://github.com/JBarmentlo/strands-agent-factory/issues)
- General Discussion: [GitHub Discussions](https://github.com/your-username/yacba/discussions)
