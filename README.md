# YACBA - Yet Another ChatBot Agent

YACBA is a command-line interface for chatting with AI models. It provides configuration management, tool integration, and saves your conversation sessions. The underlying AI capabilities come from [strands-agent-factory](https://github.com/bassmanitram/strands-agent-factory), which is built on [strands-agents](https://github.com/pydantic/strands-agents).

You can run it interactively for chat sessions, or in headless mode for automation and scripting. Configuration can be done through command-line arguments, config files with named profiles, or environment variables.

---

## Getting Started

### Quick Install (Recommended)

Download and run the YACBA launcher:

```bash
# Download launcher
curl -o yacba https://raw.githubusercontent.com/bassmanitram/yacba/main/code/yacba
chmod +x yacba

# Run installation
./yacba
```

The launcher will automatically:
- Install YACBA to `~/.yacba/`
- Set up a Python virtual environment
- Install core dependencies
- Offer to create a symlink in your PATH for easy access

After installation, you can run `yacba` from anywhere (if you created the symlink), or use `~/.yacba/bin/yacba`.

(**Note:** After installation you should remove the yacba launcher that you _originally_ downloaded)

### Install Model Providers

YACBA installs with minimal dependencies. Install model providers as needed:

```bash
# List available providers
yacba list-extras

# Install providers (you can install multiple at once)
yacba install-extras anthropic openai

# Or install the multi-provider proxy (recommended for flexibility)
yacba install-extras litellm
```

Available providers: `anthropic`, `openai`, `google`, `ollama`, `mistral`, `litellm`, `all`

### Set API Keys

Configure authentication for your chosen providers:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="..."
```

For AWS Bedrock and SageMaker:
```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION_NAME="us-east-1"
```

### Start Chatting

```bash
# Interactive chat with default model (gemini-2.5-flash via LiteLLM)
yacba

# Specify a different model
yacba -m "gpt-4o"

# With system prompt and tools
yacba -m "claude-3-5-sonnet" -s "You are a helpful assistant" -t ~/.yacba/tools/
```

### Manual Installation (Alternative)

If you prefer manual setup or want to contribute to development:

```bash
git clone https://github.com/bassmanitram/yacba.git
cd yacba
./code/yacba
```

---

**Requirements:** Python 3.10+ and git (for installation and updates)

---

## Usage

### Command Line Options

```bash
# Basic chat
yacba -m "gpt-4o" -s "You are a helpful assistant"

# With tools
yacba -m "gpt-4o" -t ./sample-tool-configs

# Non-interactive (headless mode)
yacba -m "gpt-4o" -H -i "Analyze the current directory"

# Using a saved configuration profile
yacba --profile development
```

The `-m` option specifies which model to use. Default is `"litellm:gemini/gemini-2.5-flash"`. You can also set it via config file, profile, or the `YACBA_MODEL_STRING` environment variable.

Model format examples:
- `"gpt-4o"`
- `"anthropic:claude-3-5-sonnet-20241022"`
- `"litellm:gemini/gemini-2.5-flash"`
- `"bedrock:anthropic.claude-3-sonnet-20240229-v1:0"`
- `"ollama:llama2:7b"`

The `-s` option sets a system prompt. You can provide text directly or load from a file using `@filename.txt`.

Use `-t` to specify a directory containing tool configuration files. These let the agent use tools such as file operations, shell commands, or MCP servers.

Add `-f` to upload files at startup. You can use glob patterns: `-f "*.py" "text/plain"` or `-f "docs/**/*.md" "text/markdown"`. Repeat the option for multiple patterns.

With `-H` (headless mode), YACBA reads prompts from stdin and processes them non-interactively. It sends the accumulated input and exits when it reaches EOF. You can also include `/send` on a line by itself to send a request immediately and continue accepting input, allowing for multi-turn conversations in scripts or pipelines.

The `--session-name` option lets you name your session so that conversations are automatically saved and can be resumed later.

### Common Options

```
-m, --model-string MODEL
    Which model to use (default: "litellm:gemini/gemini-2.5-flash")

-s, --system-prompt PROMPT
    System prompt text or @file.txt

-t, --tool-configs-dir DIR
    Directory with tool configuration files

-f, --files GLOB [MIMETYPE]
    Upload files matching glob (repeatable)

-H, --headless
    Non-interactive mode

-i, --initial-message TEXT
    Initial message to send (supports @file.txt)

--session-name NAME
    Name for this session (enables auto-save)

--profile PROFILE
    Use a named configuration profile

--config-file PATH
    Specify config file location

--show-config
    Display resolved configuration

--list-profiles
    List available profiles
```

For the complete list: `yacba --help`

### Model Configuration

You can fine-tune model behavior using a JSON or YAML config file:

```json
{
  "temperature": 0.7,
  "max_tokens": 2000,
  "top_p": 0.9
}
```

```bash
yacba -m "gpt-4o" --model-config ./configs/creative.json
```

You can override individual settings in the model configuration with `--mc`:

```bash
yacba -m "gpt-4o" --mc temperature:0.9 --mc max_tokens:4000
```

### Conversation Management

For long conversations, YACBA can manage context in three ways:

**No management** (`--conversation-manager-type null`): Everything stays in context. Good for short sessions or models with large context windows.

**Sliding window** (`--conversation-manager-type sliding_window`): Keeps only recent messages. Older messages are dropped. Use `--sliding-window-size` to set how many to keep (default: 40).

```bash
yacba --conversation-manager-type sliding_window --sliding-window-size 30
```

**Summarizing** (`--conversation-manager-type summarizing`): Summarizes older messages while keeping recent ones in full. Use `--preserve-recent-messages` to set how many recent messages to never summarize (default: 10), and `--summary-ratio` for how much to condense (default: 0.3).

```bash
yacba \
  --conversation-manager-type summarizing \
  --preserve-recent-messages 15 \
  --summary-ratio 0.2 \
  --summarization-model "gpt-4o-mini"
```

You can use a different (cheaper) model for summarization with `--summarization-model`, and customize the summarization prompt with `--custom-summarization-prompt`.

---

## Configuration Files

YACBA supports configuration files to reduce repetitive command-line arguments.

### Quick Start

Create a configuration file with named profiles:

```bash
cat > ~/.yacba/config.yaml << 'EOF'
profiles:
  default:
    model_string: "litellm:gemini/gemini-2.5-flash"
    tool_configs_dir: "~/.yacba/tools/"
    
  production:
    model_string: "gpt-4o"
    conversation_manager_type: summarizing
    session_name: "prod"
EOF

# Use profiles
yacba                      # Uses 'default' profile
yacba --profile production # Uses 'production' profile
```

### Configuration Locations

- `~/.yacba/config.yaml` - User-wide settings
- `./.yacba/config.yaml` - Project-specific settings (overrides user)

Both files are discovered and merged automatically.

### Quick Reference

```bash
# Use a profile
yacba --profile development

# Use simple config file
yacba --config my-settings.json

# Set via environment
export YACBA_MODEL_STRING="gpt-4o"
yacba

# Debug configuration
yacba --show-config
yacba --list-profiles
```

### Further Information

For complete configuration documentation including:
- Profile inheritance and structure
- All available configuration options
- File loading with `@filename` syntax
- Configuration precedence rules  
- Environment variable reference (all 20 variables)
- Variable interpolation
- Troubleshooting

See **[README.CONFIG.md](README.CONFIG.md)** for the complete configuration guide.

---

## Interactive Mode

When you run YACBA without `-H`, you get an interactive chat session with these commands:

- `/help` - Show available commands
- `/status` - Show session information
- `/tools` - List available tools
- `/history` - Show conversation history
- `/clear` - Clear conversation history
- `/session save [name]` - Save current session
- `/session load <name>` - Load saved session
- `/session list` - List saved sessions
- `/conversation-manager [type]` - Change conversation strategy
- `/exit` or `/quit` - Exit

The REPL provides tab completion for commands, file paths, shell variables, and command substitution.

Keyboard shortcuts:
- **Alt+Enter**: Submit your message
- **Alt+C**: Cancel running operation
- **Ctrl+C**: Cancel or exit
- **Ctrl+R**: Search history
- **F6**: Paste from clipboard (Text and images)
- **Escape+!**: Enter a shell command (type `sh`, or your prefered shell command, to drop into a shell session)


### Tab Completion Examples

The REPL provides intelligent completion:

```bash
# Command completion
/h<Tab>              # Completes to /help, /history
/se<Tab>             # Completes to /session

# File path completion
file("/tmp/<Tab>     # Shows directory contents
file("~/Doc<Tab>     # Completes to ~/Documents/

# Shell variable expansion
${HOME}<Tab>         # Expands to /home/username
${PWD}<Tab>          # Expands to current directory

# Shell command substitution
$(whoami)<Tab>       # Expands to current username
$(pwd)<Tab>          # Expands to current directory path
```
Sessions are stored in `~/.yacba/sessions/` by default.

---

## Tools

YACBA loads tools from JSON or YAML configuration files. Tools let the agent interact with systems, files, APIs, or other agents.

### Python Function Tools

Expose Python functions as tools:

```json
{
  "id": "strands-tools",
  "type": "python",
  "module_path": "strands_tools",
  "functions": ["shell", "file_read", "file_write"]
}
```

### MCP Server Tools

Connect to Model Context Protocol servers:

```json
{
  "id": "aws-mcp",
  "type": "mcp",
  "command": "uvx",
  "args": ["-q", "awslabs.aws-api-mcp-server@latest"],
  "env": {
    "FASTMCP_LOG_LEVEL": "ERROR"
  }
}
```

### A2A Tools

Connect to other AI agents as tools:

```json
{
  "id": "specialist-agents",
  "type": "a2a",
  "urls": [
    "https://research-agent.example.com",
    "https://code-agent.example.com"
  ],
  "timeout": 300
}
```

Load tools with `-t`:

```bash
yacba -t ./sample-tool-configs
```

See the `sample-tool-configs/` directory for examples. For details on creating custom tools or setting up MCP/A2A, see the [strands-agent-factory documentation](https://github.com/bassmanitram/strands-agent-factory#tools).

---

## Examples

### Chat with file context

```bash
yacba -m "gpt-4o" \
  -s "You are a code reviewer" \
  -f "*.py" "text/plain" \
  -i "Review these files"
```

### Headless automation

```bash
yacba -H \
  -i "List all TODO comments" \
  -t ./sample-tool-configs \
  -f "**/*.py" "text/plain"
```

### Long conversation with summarization

```bash
yacba -m "gpt-4o" \
  --session-name research \
  --conversation-manager-type summarizing \
  --preserve-recent-messages 20 \
  --summarization-model "gpt-4o-mini"
```

### Multiple file types

```bash
yacba \
  -f "src/**/*.py" "text/plain" \
  -f "*.md" "text/markdown" \
  -f "*.json" "application/json"
```

### Custom configuration

```bash
yacba -m "anthropic:claude-3-5-sonnet-20241022" \
  -s @prompts/assistant.txt \
  -t ./tools \
  --session-name project \
  --show-tool-use \
  --mc temperature:0.8 \
  --mc max_tokens:4000
```

---

## Troubleshooting

If you get module import errors, make sure dependencies are installed:
```bash
pip install -r requirements.txt
```

For API errors, check that your credentials are set:
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
```

For AWS Bedrock:
```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION_NAME="us-east-1"
```

(note that in a configuration profile you can specify environment variables, but it is strongly
advised that you do NOT save secrets in configuration profiles)

See [LiteLLM provider documentation](https://docs.litellm.ai/docs/providers) for other providers.

To debug configuration:
```bash
yacba --show-config
yacba --list-profiles
```

For detailed logs:
```bash
export YACBA_LOG_LEVEL=DEBUG
yacba
```

### Corrupted Sessions

If a session fails to load because of interrupted tool execution, use the repair tool:

```bash
python code/scripts/fix_strands_session.py ~/.yacba/sessions/session_name

# Preview changes first
python code/scripts/fix_strands_session.py --dry-run ~/.yacba/sessions/session_name
```

This removes orphaned tool calls (where the agent requested a tool but execution was cancelled before completion). The tool will show you what will be deleted and ask for confirmation.

---

## File Locations

YACBA uses these locations by default:

- `~/.yacba/config.yaml` - User configuration
- `./.yacba/config.yaml` - Project configuration
- `~/.yacba/sessions/` - Saved sessions
- `~/.yacba/history.txt` - Command history
- `~/.yacba/prompts/` - System prompts (by convention)
- `~/.yacba/tools/` - Tool configurations (by convention)

Example tool and model configurations are in the `sample-tool-configs/` and `sample-model-configs/` directories.

---

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details on how YACBA is structured and how it integrates with strands-agent-factory.

---

## Development

The project structure:

```
yacba/
├── code/
│   ├── yacba.py                    # Entry point
│   ├── config/                     # Configuration handling
│   ├── adapters/                   # Framework integrations
│   │   ├── strands_factory/        # strands-agent-factory adapter
│   │   └── repl_toolkit/           # REPL adapter
│   ├── utils/                      # Utilities
│   ├── scripts/                    # Maintenance tools
│   │   └── fix_strands_session.py
│   ├── sample-tool-configs/        # Example tool configs
│   ├── sample-model-configs/       # Example model configs
│   └── tests/                      # Test suite
└── README.md
```

Run tests:
```bash
cd code
python -m pytest tests/ -v
```

Contributions are welcome. For features related to core agent functionality (new tool types, conversation strategies, provider support), contribute to [strands-agent-factory](https://github.com/bassmanitram/strands-agent-factory) instead.

---

## Dependencies

YACBA uses:
- [dataclass-args](https://pypi.org/project/dataclass-args/) for CLI parsing
- [profile-config](https://pypi.org/project/profile-config/) for profile-based configuration management
- [repl-toolkit](https://pypi.org/project/repl-toolkit/) for the interactive interface
- [strands-agent-factory](https://github.com/bassmanitram/strands-agent-factory) for agent functionality
- [structlog](https://www.structlog.org/) for logging

strands-agent-factory brings in strands-agents, LiteLLM.

repl-toolkit brings in prompt-toolkit.

See `requirements.txt` for the complete list.

---

## License

MIT License - see [LICENSE](LICENSE) file.

---

## Credits

Built with [strands-agent-factory](https://github.com/bassmanitram/strands-agent-factory), [strands-agents](https://github.com/pydantic/strands-agents), [dataclass-args](https://pypi.org/project/dataclass-args/), [profile-config](https://pypi.org/project/profile-config/), [repl-toolkit](https://pypi.org/project/repl-toolkit/), [structlog](https://www.structlog.org/), and [prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit).
