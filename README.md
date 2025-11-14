# YACBA - Yet Another ChatBot Agent

YACBA is a command-line interface for chatting with AI models. It provides configuration management, tool integration, and saves your conversation sessions. The underlying AI capabilities come from [strands-agent-factory](https://github.com/JBarmentlo/strands-agent-factory), which is built on [strands-agents](https://github.com/pydantic/strands-agents).

You can run it interactively for chat sessions, or in headless mode for automation and scripting. Configuration can be done through command-line arguments, config files with named profiles, or environment variables.

---

## Getting Started

```bash
git clone https://github.com/your-username/yacba.git
cd yacba/code
pip install -r requirements.txt

# Start a chat session (uses default model: gemini-2.5-flash)
python yacba.py

# Or specify a different model
python yacba.py -m "gpt-4o"
```

You'll need Python 3.9+ and API keys for whichever model provider you use (OpenAI, Anthropic, Google, etc.).

---

## Usage

### Command Line Options

```bash
# Basic chat
python yacba.py -m "gpt-4o" -s "You are a helpful assistant"

# With tools
python yacba.py -m "gpt-4o" -t ./sample-tool-configs

# Non-interactive (headless mode)
python yacba.py -m "gpt-4o" -H -i "Analyze the current directory"

# Using a saved configuration profile
python yacba.py --profile development
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

For the complete list: `python yacba.py --help`

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
python yacba.py -m "gpt-4o" --model-config ./configs/creative.json
```

You can override individual settings in the model configuration with `--mc`:

```bash
python yacba.py -m "gpt-4o" --mc temperature:0.9 --mc max_tokens:4000
```

### Conversation Management

For long conversations, YACBA can manage context in three ways:

**No management** (`--conversation-manager-type null`): Everything stays in context. Good for short sessions or models with large context windows.

**Sliding window** (`--conversation-manager-type sliding_window`): Keeps only recent messages. Older messages are dropped. Use `--sliding-window-size` to set how many to keep (default: 40).

```bash
python yacba.py --conversation-manager-type sliding_window --sliding-window-size 30
```

**Summarizing** (`--conversation-manager-type summarizing`): Summarizes older messages while keeping recent ones in full. Use `--preserve-recent-messages` to set how many recent messages to never summarize (default: 10), and `--summary-ratio` for how much to condense (default: 0.3).

```bash
python yacba.py \
  --conversation-manager-type summarizing \
  --preserve-recent-messages 15 \
  --summary-ratio 0.2 \
  --summarization-model "gpt-4o-mini"
```

You can use a different (cheaper) model for summarization with `--summarization-model`, and customize the summarization prompt with `--custom-summarization-prompt`.

---

## Configuration Files

YACBA looks for configuration in `~/.yacba/config.yaml` or `./.yacba/config.yaml`. You can also specify a file with `--config-file`.

Configuration uses profiles - named sets of options you can switch between:

```yaml
default_profile: development

defaults:
  conversation_manager_type: sliding_window
  sliding_window_size: 40

profiles:
  development:
    model_string: "litellm:gemini/gemini-2.5-flash"
    system_prompt: "You are a development assistant"
    tool_configs_dir: "~/.yacba/tools/"
    show_tool_use: true
    
  production:
    model_string: "anthropic:claude-3-5-sonnet-20241022"
    system_prompt: "@~/.yacba/prompts/production.txt"
    conversation_manager_type: summarizing
    preserve_recent_messages: 15
    session_name: "prod-session"
    
  coding:
    inherits: development
    model_string: "gpt-4o"
    system_prompt: "You are an expert programmer"
```

Use a profile with `--profile`:

```bash
python yacba.py --profile coding
```

Configuration sources are merged in this order (highest priority first):
1. Command-line arguments
2. Config file specified with `--config-file`
3. Discovered config files
4. Environment variables (`YACBA_*`)
5. Default values

Some CLI options can be set via environment variables using the `YACBA_` prefix:

```bash
export YACBA_MODEL_STRING="gpt-4o"
export YACBA_SYSTEM_PROMPT="You are a helpful assistant"
export YACBA_SHOW_TOOL_USE="true"
```

For more details on the profile system, including advanced features like profile inheritance, variable substitution, and configuration discovery, see the [profile-config documentation](https://pypi.org/project/profile-config/).

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
- **F6**: Paste from clipboard
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
python yacba.py -t ./sample-tool-configs
```

See the `sample-tool-configs/` directory for examples. For details on creating custom tools or setting up MCP/A2A, see the [strands-agent-factory documentation](https://github.com/JBarmentlo/strands-agent-factory#tools).

---

## Examples

### Chat with file context

```bash
python yacba.py -m "gpt-4o" \
  -s "You are a code reviewer" \
  -f "*.py" "text/plain" \
  -i "Review these files"
```

### Headless automation

```bash
python yacba.py -H \
  -i "List all TODO comments" \
  -t ./sample-tool-configs \
  -f "**/*.py" "text/plain"
```

### Long conversation with summarization

```bash
python yacba.py -m "gpt-4o" \
  --session-name research \
  --conversation-manager-type summarizing \
  --preserve-recent-messages 20 \
  --summarization-model "gpt-4o-mini"
```

### Multiple file types

```bash
python yacba.py \
  -f "src/**/*.py" "text/plain" \
  -f "*.md" "text/markdown" \
  -f "*.json" "application/json"
```

### Custom configuration

```bash
python yacba.py -m "anthropic:claude-3-5-sonnet-20241022" \
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
python yacba.py --show-config
python yacba.py --list-profiles
```

For detailed logs:
```bash
export YACBA_LOG_LEVEL=DEBUG
python yacba.py
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

## Environment Variables

All configuration options can be set via environment variables with the `YACBA_` prefix:

```bash
YACBA_MODEL_STRING="gpt-4o"
YACBA_SYSTEM_PROMPT="You are a helpful assistant"
YACBA_TOOL_CONFIGS_DIR="./tools"
YACBA_SESSION_NAME="my-session"
YACBA_SHOW_TOOL_USE="true"
YACBA_HEADLESS="false"
```

Logging control:
```bash
YACBA_LOG_LEVEL=DEBUG          # DEBUG, INFO, WARNING, ERROR
YACBA_LOG_TRACEBACKS=false     # Show/hide exception tracebacks
YACBA_LOG_JSON=true            # JSON formatted logs
```

Provider API keys:
```bash
OPENAI_API_KEY="..."
ANTHROPIC_API_KEY="..."
GOOGLE_API_KEY="..."
AWS_ACCESS_KEY_ID="..."
AWS_SECRET_ACCESS_KEY="..."
AWS_REGION_NAME="..."
```

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

Contributions are welcome. For features related to core agent functionality (new tool types, conversation strategies, provider support), contribute to [strands-agent-factory](https://github.com/JBarmentlo/strands-agent-factory) instead.

---

## Dependencies

YACBA uses:
- [dataclass-args](https://pypi.org/project/dataclass-args/) for CLI parsing
- [profile-config](https://pypi.org/project/profile-config/) for configuration management
- [repl-toolkit](https://pypi.org/project/repl-toolkit/) for the interactive interface
- [strands-agent-factory](https://github.com/JBarmentlo/strands-agent-factory) for agent functionality
- [structlog](https://www.structlog.org/) for logging

strands-agent-factory brings in strands-agents, LiteLLM, and prompt_toolkit.

See `requirements.txt` for the complete list.

---

## License

MIT License - see [LICENSE](LICENSE) file.

---

## Credits

Built with [strands-agent-factory](https://github.com/JBarmentlo/strands-agent-factory), [strands-agents](https://github.com/pydantic/strands-agents), [dataclass-args](https://pypi.org/project/dataclass-args/), [profile-config](https://pypi.org/project/profile-config/), [repl-toolkit](https://pypi.org/project/repl-toolkit/), [structlog](https://www.structlog.org/), and [prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit).
