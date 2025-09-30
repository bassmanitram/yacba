# YACBA: Yet Another ChatBot Agent

**Tagline:** A flexible and configurable command-line AI agent for interactive chat, headless scripting, and advanced LLM interactions.

## Overview

YACBA is a powerful command-line interface (CLI) tool designed to streamline your interactions with large language models (LLMs). Built upon the `strands-agents` library, it offers both an engaging interactive chatbot experience and a robust headless mode for automation and scripting. YACBA supports a wide range of LLM frameworks, provides intelligent conversation management, robust file handling, and a sophisticated configuration system to tailor the agent's behavior to your specific needs.

## Features

*   **Dual Operating Modes:**
    *   **Interactive Chatbot:** Engage in multi-turn conversations with rich CLI features, command history, and real-time streaming responses.
    *   **Headless Scripting:** Integrate YACBA into your scripts and pipelines for automated tasks, processing initial messages and streaming responses to `stdout`.
*   **Broad LLM Support:** Seamlessly connect to models from `litellm`, `openai`, `anthropic`, `bedrock`, and more, with automatic framework detection.
*   **Extensible Tool Integration:** Expand the agent's capabilities by dynamically loading tools from:
    *   **MCP Servers:** Integrate with local or remote Model Context Protocol (MCP) servers (stdio, HTTP).
    *   **Local Python Modules:** Define and use your own Python functions decorated with `@tool`.
*   **Advanced Conversation Management:** Efficiently handle long conversations and context windows with:
    *   **Sliding Window:** Maintain a configurable window of recent messages.
    *   **Summarization:** Intelligently summarize older context to preserve information without exceeding token limits.
    *   **Null Mode:** Keep full conversation history for short sessions or debugging.
*   **Comprehensive File Handling:**
    *   **Startup Uploads:** Upload individual files or entire directories (with glob filters) at launch.
    *   **In-Chat Uploads:** Upload files or directories during a conversation using `file('path/to/file')` syntax.
*   **Powerful Configuration System:**
    *   **Profile-Based Settings:** Define reusable YAML or JSON configuration profiles for different use cases (development, production, coding) that can inherit settings from one another.
    *   **Global Defaults & Overrides:** Set global defaults and apply specific overrides via command-line arguments, JSON/YAML model config files, or directly within profiles.
    *   **Template Variables:** Use dynamic variables like `${PROJECT_NAME}` and environment variables in your configurations.
    *   **For comprehensive details on the configuration system, see [README.CONFIG.md](README.CONFIG.md).**
    *   **For detailed information on fine-tuning model parameters, see [README.MODEL_CONFIG.md](README.MODEL_CONFIG.md).**
*   **Rich CLI Experience:** Persistent command history, interactive path auto-completion, real-time streaming responses, and useful meta-commands (`/clear`, `/tools`, `/help`).
*   **Conversation Persistence:** Save and load conversation history across sessions using named sessions.
*   **Performance Tuning:** Built-in caching for repeated tasks, with options to disable or clear the cache and display performance statistics.

## Installation

1.  **Clone the repository (or download the source files).**
2.  Change to the code directory:
    ```bash
    cd yacba/code
    ```
3.  Create and activate a Python virtual environment (recommended):
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
4.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
5.  **Set up your environment variables.** You will need to configure API keys for your chosen model frameworks (e.g., `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) and/or set up your AWS credentials for Bedrock.

## How to Run

The main entry point for the application is `yacba.py`. A convenience shell script, `yacba`, is also provided and recommended as it automatically finds `yacba.py` and suppresses noisy warnings.

**To make the `yacba` script executable:**
```bash
chmod +x yacba
```

**To make `yacba` available everywhere (Optional):**
You can create a symbolic link to the `yacba` script in a directory that is in your system's `PATH`.
```bash
# Example for /usr/local/bin:
sudo ln -s /path/to/your/yacba/code/yacba /usr/local/bin/yacba
```
After creating the link, you can simply run `yacba` from any terminal.

### Interactive Chatbot Mode

To start a standard interactive chat session:
```bash
yacba
```
You can exit the chat by typing `/exit` or `/quit`, or by pressing `Ctrl+D`. Use `Enter` to add a new line to your input, and `Alt-Enter` to send your input to the LLM. For a list of in-chat commands, type `/help`.

### Headless Mode

Headless mode is designed for scripting. It takes an initial message, streams the agent's response directly to `stdout`, and then exits.

**Using the `-i` flag:**
```bash
yacba --headless -i "Summarize the main points of Moby Dick."
```

**Piping from `stdin`:**
```bash
cat report.txt | yacba --headless
```

## Configuration

YACBA features a robust and flexible configuration system using YAML or JSON files and profiles. This allows you to define reusable setups for different tasks and environments, eliminating the need for long command-line arguments.

### Quick Start with Configuration

1.  **Generate a Sample Configuration:**
    ```bash
    yacba --init-config ~/.yacba/config.yaml
    ```
    This creates a global configuration file with default settings and examples. You can also create project-specific configurations at `./.yacba/config.yaml` or `./.yacba/config.json`.

2.  **Edit Your Configuration:**
    Open the generated `config.yaml` or `config.json` and customize profiles, models, tools, and other settings.

    ```yaml
    # ~/.yacba/config.yaml example
    default_profile: "my-default"

    profiles:
      my-default:
        model: "litellm:gemini/gemini-1.5-flash"
        tool_configs:
          - "~/my-tools/"
        system_prompt: "You are my personal assistant."

      coding:
        inherits: "my-default"
        model: "anthropic:claude-3-sonnet"
        tool_configs:
          - "./project-tools/"
        files: ["README.md", "src/"]
        system_prompt: "You are an expert programmer."
    ```

3.  **Use Profiles:**
    ```bash
    # Use your default profile
    yacba

    # Switch to a specific profile
    yacba --profile coding

    # Override profile settings on the fly
    yacba --profile coding --model "openai:gpt-4"
    ```

For comprehensive details on the configuration system, including file discovery, structure, inheritance, template variables, and CLI commands, please refer to [**README.CONFIG.md**](README.CONFIG.md).

### Model-Specific Configuration

YACBA allows fine-grained control over LLM parameters such as `temperature`, `max_tokens`, `response_format`, and `safety_settings`. These can be set via JSON or YAML configuration files, or directly from the command line.

**Example using a YAML config file (`openai-gpt4.yaml`):**
```yaml
# sample-model-configs/openai-gpt4.yaml
temperature: 0.8
max_tokens: 4096
top_p: 0.95
presence_penalty: 0.1
frequency_penalty: 0.0
response_format:
  type: "text"
stop: null
```
```bash
yacba --model-config sample-model-configs/openai-gpt4.yaml
```

**Example using command-line overrides:**
```bash
yacba --model-config sample-model-configs/openai-gpt4.yaml -c temperature:0.8 -c response_format.type:json_object
```

For more in-depth information and framework-specific examples (OpenAI, Anthropic, Gemini), see [**README.MODEL_CONFIG.md**](README.MODEL_CONFIG.md).

## Configuring Tools

You can extend YACBA's capabilities by integrating external tools. The agent automatically discovers and loads tools from `.tools.json` or `.tools.yaml` files within specified directories.

### Type 1: MCP Servers (`type: "mcp"`)

Connect to external processes that implement the Model Context Protocol (MCP). YACBA supports `stdio` and `http` transports.

**Example `aws-cli-stdio.tools.yaml` (stdio transport):**```yaml
# my-aws-tools-dir/aws-cli-stdio.tools.yaml
id: "awslabs.aws-api-mcp-server"
type: "mcp"
command: "uvx"
args:
  - "-q"
  - "awslabs.aws-api-mcp-server@latest"
```

**Example `some-service-http.tools.json` (http transport):**
```json
{
  "id": "some-remote-service",
  "type": "mcp",
  "url": "http://localhost:8080/mcp"
}
```

### Type 2: Python Modules (`type: "python"`)

Load tools directly from functions in a local Python file. Functions must be decorated with `@tool` (from `strands-agents`). The `module_path` is relative to the `.tools.json` or `.tools.yaml` file.

**Example `local-files.tools.yaml`:**
```yaml
# ./project-tools/local-files.tools.yaml
id: "local-file-lister"
type: "python"
module_path: "../sample-python-tools/local_tools.py"
functions:
  - "list_files"
```

**Example `strands.tools.json`:**
```json
{
  "id": "strands-tools",
  "type": "python",
  "module_path": "strands_tools",
  "functions": ["shell", "file_read", "file_write"],
  "disabled": false
}
```

## Conversation Management

YACBA offers intelligent strategies to manage conversation history and model context limits.

### Sliding Window Mode (Default)

Keeps a configurable number of recent messages. Older messages are discarded.

```bash
# Use sliding window with 60 messages
yacba --conversation-manager sliding_window --window-size 60
```
**Best for:** General conversations, development sessions.

### Summarizing Mode

Intelligently summarizes older conversation context, preserving important information while keeping the overall context size manageable.

```bash
# Use summarizing with default settings
yacba --conversation-manager summarizing

# Custom summarization settings
yacba --conversation-manager summarizing \
  --summary-ratio 0.4 \
  --preserve-recent 15 \
  --summarization-model "litellm:gemini/gemini-1.5-flash"
```
**Best for:** Long research sessions, complex projects where historical context is crucial.

### Null Mode

Disables conversation management, keeping the full conversation history in memory.
```bash
# Disable conversation management
yacba --conversation-manager null
```
**Best for:** Short sessions, debugging, or when complete message history is essential.

## Command-Line Options

YACBA's behavior can be extensively configured via command-line flags. Many of these options can also be set within YAML or JSON configuration profiles (see [**README.CONFIG.md**](README.CONFIG.md)) for more persistent and organized settings.

| Flag(s) | Argument Name | Description |
| :------ | :------------ | :---------- |
| `-m`, `--model` | `model` | The model to use, in `<framework>:<model_id>` format (e.g., `openai:gpt-4o`). If the framework is omitted, it will be guessed. Defaults to the `YACBA_MODEL_ID` environment variable or `litellm:gemini/gemini-2.5-flash`. |
| `--model-config` | `model_config` | Path to a JSON or YAML file containing model configuration (e.g., `temperature`, `max_tokens`). See [**README.MODEL_CONFIG.md**](README.MODEL_CONFIG.md) for details. |
| `-c`, `--config-override` | `config_override` | Override a specific model configuration property. Format: `'property.path: value'`. Can be used multiple times. Overrides values from `--model-config`. |
| `-s`, `--system-prompt` | `system_prompt` | System prompt for the agent. Can be a string or a file URI (e.g., `@/path/to/prompt.txt`). Can also be set via the `YACBA_SYSTEM_PROMPT` environment variable. |
| `--emulate-system-prompt` | `emulate_system_prompt` | Emulate the system prompt as a user message for models that don't natively support system prompts. (Flag, no value needed). |
| `-t`, `--tool-configs-dir` | `tool_configs_dir` | Path to a directory containing tool configuration files (`*.tools.json` or `*.tools.yaml`). If specified without a path, disables tool discovery from default locations. |
| `-f`, `--files` | `files` | Files or directories to upload and analyze. Can be specified multiple times. <br/>Syntax: `-f PATH [MIMETYPE]` or, for directories, `-f 'my_dir[*.py,*.js]'` to scan with glob filters. |
| `--max-files` | `max_files` | Maximum number of files to process via `-f` and in-chat `file()`. Default: `10`. |
| `--session` | `session` | Session name for conversation persistence. If provided, YACBA will load history from `<name>.yacba-session.json` on startup and save to it on exit (in the CWD). |
| `--agent-id` | `agent_id` | Custom agent identifier for this session, used for namespacing. |
| `--conversation-manager` | `conversation_manager` | Choose conversation management strategy. <br/>`null`: disables management (keeps full history). <br/>`sliding_window`: (default) keeps a fixed number of recent messages. <br/>`summarizing`: creates summaries of older context. |
| `--window-size` | `window_size` | Maximum number of messages in `sliding_window` mode. Default: `40`. |
| `--preserve-recent` | `preserve_recent` | Number of recent messages to always preserve in `summarizing` mode. Default: `10`. |
| `--summary-ratio` | `summary_ratio` | Ratio of messages to summarize vs. keep (0.1-0.8) in `summarizing` mode. Default: `0.3`. |
| `--summarization-model` | `summarization_model` | Optional separate model for summarization (e.g., `litellm:gemini/gemini-1.5-flash` for cheaper summaries). |
| `--custom-summarization-prompt` | `custom_summarization_prompt` | Custom system prompt for summarization. If not provided, YACBA uses a built-in prompt. |
| `--no-truncate-results` | `no_truncate_results` | Disable truncation of tool results when the context window is exceeded. (Flag, no value needed). |
| `-i`, `--initial-message` | `initial_message` | An initial message to send to the agent at startup. In headless mode, if this is omitted, the message is read from `stdin`. Can be a string or a file URI (e.g., `@/path/to/message.txt`). |
| `-H`, `--headless` | `headless` | Run in headless (non-interactive) mode. Requires an `--initial-message` to be provided or piped via `stdin`. (Flag, no value needed). |
| `--show-tool-use` | `show_tool_use` | Show detailed tool execution feedback in the console. By default, tool use details are hidden for cleaner output. (Flag, no value needed). |
| `--clear-cache` | `clear_cache` | Clear the performance cache before starting the application. (Flag, no value needed). |
| `--profile` | `profile` | Use a named profile from the discovered configuration files (e.g., `--profile development`). |
| `--config` | `config` | Path to a specific configuration file (YAML or JSON) to use (e.g., `--config /path/to/my.yaml`). Overrides default discovery. |
| `--list-profiles` | `list_profiles` | List all available profiles from discovered configuration files and exit. (Flag, no value needed). |
| `--show-config` | `show_config` | Display the full resolved configuration for the current run and exit. Useful for debugging. (Flag, no value needed). |
| `--init-config` | `init_config` | Create a sample configuration file (YAML by default) at the specified path (e.g., `--init-config ~/.yacba/config.yaml`). |

## Interactive Meta-Commands

While in an interactive session, use these commands:

| Command | Description |
| :--- | :--- |
| `/clear` | Clear the agent's current conversation history. |
| `/conversation-manager` | Display current conversation management configuration. |
| `/conversation-stats` | Show conversation statistics (message counts, memory usage). |
| `/exit`, `/quit` | Exit the application. |
| `/help` | Show the list of available meta-commands. |
| `/history` | Print the current conversation history as a JSON object. |
| `/session [_LIST|name]` | With no argument, indicates the current session; `_LIST` lists avaliable sessions; `name` switches to the named session|
| `/tools` | List the names of all tools currently available to the agent. |

## Advanced Examples

### 1. Code Analysis with a Project Profile

Use a `coding` profile to analyze a Python project with specific tools and files, leveraging model configuration for quality.

```bash
# Assuming you have a project-specific .yacba/config.yaml like:
# profiles:
#   coding:
#     model: "anthropic:claude-3-sonnet"
#     system_prompt: "You are an expert software engineer. Analyze this codebase for improvements."
#     tool_configs: ["./tools/", "~/.yacba/tools/dev/"]
#     files: ["src/**/*.py", "README.md"]
#     model_config: "sample-model-configs/claude-precise.yaml" # e.g., low temperature

yacba --profile coding -i "Perform a security audit of the `src` directory."
```

### 2. Long Research Session with Summarization and Custom Prompt

Start a research session that intelligently summarizes older context, uses a cheaper model for summaries, and applies a custom system prompt for the main model.

```bash
yacba \
  --profile research-analyst \
  --conversation-manager summarizing \
  --summary-ratio 0.3 \
  --preserve-recent 15 \
  --summarization-model "litellm:gemini/gemini-1.5-flash" \
  -s "You are a meticulous research assistant. Provide concise and accurate information." \
  --session "quantum-computing-research"
```

### 3. Headless Scripting for AWS S3 Listing (with MCP Tool)

Use headless mode to query AWS S3 buckets via an MCP tool, piping the output to a file.

```bash
# Assuming you have an 'aws-cli' profile in your config.yaml:
# profiles:
#   aws-cli:
#     model: "bedrock:anthropic.claude-3-sonnet-20240229-v1:0"
#     tool_configs: ["./my-aws-tools-dir/"] # Contains aws-cli-stdio.tools.json or .tools.yaml
#     show_tool_use: false

yacba --profile aws-cli --headless \
  -i "Using my AWS tools, list all of my S3 buckets in the us-east-1 region." > s3_buckets.txt
```

### 4. Development Session with File Uploads and Performance Tracking

Set up a development session for a specific project, uploading relevant code files and tracking performance.

```bash
yacba --profile development \
  -f "src/[*.py,*.js]" \
  -f "docs/*.md" \
  --session "my-web-app-dev" \
  --show-perf-stats
```
