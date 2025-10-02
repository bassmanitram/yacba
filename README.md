# YACBA: Yet Another ChatBot Agent

A flexible, configurable command-line AI agent framework for interactive chat, headless automation, and advanced LLM integrations with extensible tool support.

## Overview

YACBA is a sophisticated Python-based CLI tool that provides seamless interaction with large language models (LLMs). Built on the `strands-agents` framework, it offers both interactive chatbot experiences and headless automation capabilities. YACBA supports multiple LLM providers, intelligent conversation management, comprehensive file handling, and a powerful plugin system for extending functionality.

## Key Features

### 🚀 **Dual Operation Modes**
- **Interactive Mode**: Rich CLI experience with real-time streaming, command history, and meta-commands
- **Headless Mode**: Scriptable automation for CI/CD pipelines and batch processing

### 🧠 **Universal LLM Support**
- **Framework Agnostic**: Works with OpenAI, Anthropic, Google Gemini, AWS Bedrock, and any LiteLLM-compatible provider
- **Auto-Detection**: Intelligent framework detection from model strings
- **Custom Configuration**: Fine-grained control over model parameters (temperature, tokens, safety settings)

### 🔧 **Extensible Tool System**
- **MCP Integration**: Connect to Model Context Protocol servers (stdio/HTTP)
- **Python Modules**: Load custom tools from decorated Python functions
- **Hot Discovery**: Automatic tool loading from configuration directories
- **Sample Tools**: Includes file operations, shell access, and AWS utilities

### 💬 **Intelligent Conversation Management**
- **Sliding Window**: Keep recent N messages for active conversations
- **Summarization**: AI-powered context compression for long sessions
- **Session Persistence**: Save and restore conversation history
- **Context Optimization**: Automatic handling of token limits

### 📁 **Advanced File Handling**
- **Bulk Upload**: Process files and directories at startup
- **Glob Patterns**: Filter files using wildcards (e.g., `src/**/*.py`)
- **In-Chat Upload**: Dynamic file addition using `file('path')` syntax
- **MIME Detection**: Automatic content type recognition

### ⚙️ **Configuration System**
- **Profile-Based**: Reusable YAML/JSON configurations for different contexts
- **Inheritance**: Profiles can extend other profiles
- **Template Variables**: Dynamic substitution with environment variables
- **CLI Override**: Command-line arguments take precedence

## Installation

### Prerequisites
- Python 3.8+
- API keys for your chosen LLM provider(s)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd yacba/code
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API access**
   ```bash
   # Example for Gemini
   export GEMINI_API_KEY="your-api-key-here"
   
   # Example for OpenAI
   export OPENAI_API_KEY="your-api-key-here"
   
   # Example for Anthropic
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

5. **Make executable** (optional)
   ```bash
   chmod +x yacba
   # Create system-wide link
   sudo ln -s $(pwd)/yacba /usr/local/bin/yacba
   ```

## Quick Start

### Interactive Chat
```bash
# Basic chat with default model
./yacba

# Use specific model
./yacba --model "openai:gpt-4"

# Load files for analysis
./yacba --files "src/**/*.py" --files "README.md"
```

### Headless Automation
```bash
# Single query
./yacba --headless -i "Explain the main function in this codebase" --files "main.py"

# Pipeline integration
echo "Summarize this log file" | ./yacba --headless --files "error.log"

# Multi-message with /send delimiter
cat << 'EOF' | ./yacba --headless
Analyze this Python code for security issues.

/send

Now suggest improvements for performance.
EOF
```

## Configuration

### Quick Configuration Setup

1. **Generate sample config**
   ```bash
   ./yacba --init-config ~/.yacba/config.yaml
   ```

2. **Create profiles for different use cases**
   ```yaml
   # ~/.yacba/config.yaml
   default_profile: "development"
   
   profiles:
     development:
       model: "litellm:gemini/gemini-1.5-flash"
       system_prompt: "You are a helpful development assistant."
       tool_configs: ["./tools/"]
       conversation_manager: "sliding_window"
       window_size: 40
     
     production:
       model: "openai:gpt-4"
       system_prompt: "You are a production support agent."
       tool_configs: ["~/.yacba/tools/prod/"]
       conversation_manager: "summarizing"
       session: "prod-session"
   ```

3. **Use profiles**
   ```bash
   # Use default profile
   ./yacba
   
   # Switch profiles
   ./yacba --profile production
   
   # Override settings
   ./yacba --profile development --model "anthropic:claude-3-sonnet"
   ```

For comprehensive details on the configuration system, including file discovery, inheritance, template variables, and advanced features, see [**README.CONFIG.md**](README.CONFIG.md).

### Model Configuration

Control LLM behavior with configuration files:

```json
// model-configs/precise.json
{
  "temperature": 0.1,
  "max_tokens": 4096,
  "top_p": 0.9,
  "response_format": {"type": "json_object"}
}
```

```bash
./yacba --model-config model-configs/precise.json
```

For comprehensive details on model configuration options and framework-specific examples, see [**README.MODEL_CONFIG.md**](README.MODEL_CONFIG.md).

## Tool Integration

### MCP Server Tools

Connect external MCP servers for enhanced capabilities:

```yaml
# tools/aws-cli.tools.yaml
id: "aws-api-server"
type: "mcp"
command: "uvx"
args: ["-q", "awslabs.aws-api-mcp-server@latest"]
```

### Python Function Tools

Create custom tools from Python functions:

```python
# tools/custom_tools.py
from strands_agents import tool

@tool
def analyze_code(file_path: str) -> str:
    """Analyze Python code for complexity."""
    # Your implementation here
    return f"Analysis of {file_path}: ..."
```

```yaml
# tools/custom.tools.yaml
id: "custom-tools"
type: "python"
module_path: "custom_tools"
functions: ["analyze_code"]
```

## Advanced Usage Examples

### Development Workflow
```bash
# Set up development session with project files
./yacba --profile coding \
  --files "src/**/*.py" \
  --files "tests/**/*.py" \
  --files "README.md" \
  --session "myproject-dev" \
  --conversation-manager summarizing
```

### Automated Code Review
```bash
# Headless code analysis pipeline
./yacba --headless \
  --model "anthropic:claude-3-sonnet" \
  --files "src/" \
  --initial-message "Perform a comprehensive code review focusing on security, performance, and maintainability." \
  > code-review-report.md
```

### Research Session with Context Management
```bash
# Long research session with intelligent summarization
./yacba --profile research \
  --conversation-manager summarizing \
  --preserve-recent 10 \
  --summary-ratio 0.3 \
  --summarization-model "litellm:gemini/gemini-1.5-flash" \
  --session "ai-research-$(date +%Y%m%d)"
```

## Interactive Commands

While in interactive mode, use these meta-commands:

| Command | Description |
|---------|-------------|
| `/clear` | Clear conversation history |
| `/exit`, `/quit` | Exit application |
| `/help` | Show available commands |
| `/history` | Display conversation as JSON |
| `/session [name]` | Switch or list sessions |
| `/tools` | List available tools |
| `/conversation-manager` | Show conversation management info |
| `/conversation-stats` | Display usage statistics |

## Command-Line Reference

### Core Options

| Flag(s) | Description | Default | Example |
|---------|-------------|---------|---------|
| `-m`, `--model` | Model specification | `litellm:gemini/gemini-2.5-flash` | `--model "openai:gpt-4"` |
| `--model-config` | Path to model configuration file | None | `--model-config configs/precise.json` |
| `-c`, `--config-override` | Override model config (repeatable) | None | `-c temperature:0.8 -c max_tokens:4096` |
| `-s`, `--system-prompt` | System prompt text or `@file` reference | Built-in assistant prompt | `-s "You are a code reviewer"` |
| `--emulate-system-prompt` | Emulate system prompt as user message | `false` | `--emulate-system-prompt` |
| `-t`, `--tool-configs-dir` | Tool configuration directory | Auto-discovered | `-t ./my-tools/` |
| `-f`, `--files` | Files/directories with optional MIME type | None | `-f "src/**/*.py" -f "config.json text/plain"` |
| `-i`, `--initial-message` | Initial message or `@file` reference | None | `-i "Analyze this codebase"` |
| `-H`, `--headless` | Non-interactive mode | `false` | `--headless` |

### Configuration Management

| Flag(s) | Description | Default | Example |
|---------|-------------|---------|---------|
| `--profile` | Use named configuration profile | `default_profile` from config | `--profile development` |
| `--config` | Specific configuration file path | Auto-discovered | `--config ~/.yacba/myconfig.yaml` |
| `--list-profiles` | Show available profiles and exit | N/A | `--list-profiles` |
| `--show-config` | Display resolved configuration and exit | N/A | `--show-config` |
| `--init-config` | Create sample configuration file | N/A | `--init-config ~/.yacba/config.yaml` |

### Conversation Management

| Flag(s) | Description | Default | Example |
|---------|-------------|---------|---------|
| `--conversation-manager` | Management strategy | `sliding_window` | `--conversation-manager summarizing` |
| `--window-size` | Messages to keep in sliding window | `40` | `--window-size 60` |
| `--preserve-recent` | Recent messages to preserve in summarizing | `10` | `--preserve-recent 15` |
| `--summary-ratio` | Summarization ratio (0.1-0.8) | `0.3` | `--summary-ratio 0.4` |
| `--summarization-model` | Separate model for summaries | Same as main model | `--summarization-model "litellm:gemini/gemini-1.5-flash"` |
| `--custom-summarization-prompt` | Custom summarization system prompt | Built-in prompt | `--custom-summarization-prompt "Summarize briefly"` |
| `--no-truncate-results` | Disable tool result truncation | `false` | `--no-truncate-results` |

### Session & Identity

| Flag(s) | Description | Default | Example |
|---------|-------------|---------|---------|
| `--session` | Named session for persistence | None | `--session "project-review"` |
| `--agent-id` | Custom agent identifier for namespacing | Auto-generated | `--agent-id "code-assistant"` |
| `--max-files` | Maximum files to process | `10` | `--max-files 50` |

### User Interface

| Flag(s) | Description | Default | Example |
|---------|-------------|---------|---------|
| `--cli-prompt` | Custom input prompt with HTML formatting | `<b><ansigreen>You:</ansigreen></b> ` | `--cli-prompt "<blue>User: </blue>"` |
| `--response-prefix` | Custom response prefix with HTML formatting | `<b><darkcyan>Chatbot:</darkcyan></b> ` | `--response-prefix "<green>AI: </green>"` |
| `--show-tool-use` | Display detailed tool execution | `false` | `--show-tool-use` |
| `--clear-cache` | Clear performance cache | `false` | `--clear-cache` |


## Architecture

YACBA is built with a modular architecture:

- **Core Engine**: Conversation management and model interaction
- **Adapters**: Framework-specific implementations (OpenAI, Anthropic, Bedrock, etc.)
- **Tool System**: MCP and Python function integration
- **CLI Interface**: Interactive and headless modes
- **Configuration**: Profile-based settings management
- **Utilities**: File processing, caching, and content handling

## Dependencies

- `strands-agents`: Core agent framework
- `strands-mcp`: Model Context Protocol support  
- `litellm`: Universal LLM API wrapper
- `loguru`: Structured logging
- `prompt-toolkit`: Rich CLI interface
- `pyyaml`: Configuration file parsing

## Contributing

YACBA welcomes contributions! The codebase is well-structured with:
- Comprehensive type hints
- Modular design for easy extension
- Extensive test coverage
- Clear separation of concerns

## License

See [LICENSE](LICENSE) file for details.

---

**YACBA** - Because sometimes you need *Yet Another ChatBot Agent* with a silly name that actually does what you want.
