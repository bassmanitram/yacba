# **Yet Another ChatBot Agent (yacba)**

Yacba provides a flexible and configurable command-line AI agent powered by the **strands-agents** library. It can be run as an interactive, multi-turn chatbot with advanced features like file uploads and tool integration, or as a non-interactive "headless" agent for use in command pipelines and scripts.

## **Features**

*   **Dual Modes:** Seamlessly switch between an interactive chatbot experience (`./yacba`) and a non-interactive headless mode (`./yacba --headless`) for scripting and automation.
*   **Multi-Framework Model Support:** Connect to any model framework supported by strands-agents, including `litellm`, `openai`, `anthropic`, and `bedrock`. The framework can be guessed automatically if not specified (e.g., `-m gemini/gemini-1.5-flash`).
*   **Extensible Tool Integration:** Dynamically load tools for the agent from various sources:
    *   **MCP Servers:** Connect to tools provided by local or remote Model Context Protocol (MCP) servers over `stdio` or `http`.
    *   **Local Python Modules:** Integrate your own Python functions decorated with `@tool`.
*   **Advanced File Handling:**
    *   **Startup Uploads:** Upload multiple files or entire directories at startup using the `-f` flag.
        *   Recursively scans directories with optional glob filters (e.g., `-f my_dir[*.py,*.js]`).
        *   Supports overriding the detected mimetype for uploaded files.
    *   **In-Chat Uploads:** Upload files during a conversation using the `file('path/to/file')` syntax. This also supports uploading entire directories and using glob filters, just like the `-f` flag.
*   **Rich CLI Experience:**
    *   **Persistent Command History:** Navigate previous inputs with arrow keys.
    *   **Real-time Streaming Responses:** Receive model responses as they are generated.
    *   **Interactive Path Auto-completion:** Press `Tab` for path suggestions when typing `file('` in chat.
    *   **Interactive Meta-Commands:** Control the application with commands like `/save`, `/clear`, `/history`, `/tools`, and `/help`.
*   **Highly Configurable:**
    *   Customize the agent's behavior with system prompts (string or loaded from a `file://` URI).
    *   Use the `-l/--legacy-prompt` flag for models that don't support system prompts natively.
    *   Specify different models and provide model-specific configurations via `--model-config` JSON files or individual `-c KEY:VALUE` flags.
    *   Control tool verbosity with `--show-tool-use`.
*   **Conversation Persistence:**
    *   Save and load conversation history using the `--session-name` flag, allowing you to resume sessions later.
*   **Performance Tuning:**
    *   Improve performance for repeated tasks with a built-in cache.
    *   Manage the cache with `--disable-cache` and `--clear-cache`.
    *   Analyze performance with `--show-perf-stats`.

## **Installation**

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
5.  **Set up your environment variables.** You will need to configure API keys for your chosen model framework (e.g., `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) and/or set up your AWS credentials for Bedrock.

## **How to Run**

The main entry point for the application is `yacba.py`. A convenience shell script, `yacba`, is also provided.

### **Using the `yacba` Shell Script**

The `yacba` script is the recommended way to run the application. It automatically finds the `yacba.py` script and suppresses common, noisy warnings from the underlying `litellm` library.

**To make it executable:**
```bash
chmod +x yacba
```

**To make `yacba` available everywhere (Optional):**
You can create a symbolic link to the `yacba` script in a directory that is in your system's `PATH`.

```bash
# Make sure the target directory (e.g., /usr/local/bin) exists and is in your PATH
sudo ln -s /path/to/your/yacba/code/yacba /usr/local/bin/yacba
```

After creating the link, you can simply run `yacba` from any terminal.

### **Interactive Chatbot Mode**

To start a standard interactive chat session:

```bash
./yacba
```

You can exit the chat by typing `/exit` or `/quit`, or by pressing `Ctrl+D`. Use `Alt+Enter` to add a new line to your input. For a list of in-chat commands, type `/help`.

### **Headless Mode**

Headless mode is designed for scripting. It takes an initial message, streams the agent's response directly to `stdout`, and then exits.

**Using the `-i` flag:**
```bash
./yacba --headless -i "Summarize the main points of Moby Dick."
```

**Piping from `stdin`:**
```bash
cat report.txt | ./yacba --headless
```

## **Command-Line Options**

| Flag | Description |
| :--- | :--- |
| `-p`, `--prompt` | Sets the system prompt. Can be a string or a file URI (e.g., `file:///path/to/prompt.txt`). |
| `-m`, `--model` | Specifies the model in `framework:model_id` format (e.g., `openai:gpt-4o`). If the framework is omitted, it will be guessed. Defaults to `YACBA_MODEL_ID` env var or `litellm:gemini/gemini-1.5-flash`. |
| `-f`, `--file` | Uploads a file or a directory. Can be used multiple times. <br/>Syntax: `-f PATH [MIMETYPE]` or, for directories, `-f 'my_dir[*.py,*.js]'` scans with glob filters. |
| `--max-files` | Maximum number of files to upload via `-f` and in-chat `file()`. Default: 20. |
| `-t`, `--tools` | Directory to load tool configurations (`*.tools.json`) from. Defaults to the current directory (`.`). If specified without a path, disables tool discovery. |
| `-i`, `--initial-message` | An initial message to send to the agent. In headless mode, if this is omitted, the message is read from `stdin`. |
| `--session-name` | Load a session history on startup and save it on exit. The file is named `<name>.yacba-session.json` in the CWD. |
| `--headless` | Activates non-interactive headless mode. |
| `--model-config` | Path to a JSON file with ad-hoc configuration for the model (e.g., `temperature`, `max_tokens`). |
| `-c`, `--config-val` | Set a single model configuration value (e.g.,`-c temperature:0.8`). Overrides values from `--model-config`. |
| `-l`, `--legacy-prompt` | Use legacy mode for system prompts by injecting it into the first user message. For models that do not support native system prompts. |
| `--show-tool-use` | Show verbose tool execution feedback in the console. By default, tool use details are hidden for cleaner output. |
| `--clear-cache` | Clears the performance cache before starting. |
| `--show-perf-stats` | Displays performance statistics (timings, cache hits/misses) on exit. |
| `--disable-cache` | Disables the performance cache for the current run. |

## **Interactive Meta-Commands**

While in an interactive session, you can use the following commands:

| Command | Description |
| :--- | :--- |
| `/help` | Show the list of available meta-commands. |
| `/save [name]` | Manually saves the current session. If `name` is provided, it sets or changes the session name before saving. |
| `/clear` | Clear the agent's current conversation history and start fresh. |
| `/history` | Print the current conversation history as a JSON object. |
| `/tools` | List the names of all tools currently available to the agent. |
| `/exit`, `/quit` | Exit the application. |

## **Configuring Tools**

You can extend the agent's capabilities by connecting it to tools. The application automatically discovers and loads tools from `.tools.json` files in the directory specified by the `-t/--tools` flag.

### **Type 1: MCP Servers (`type: "mcp"`)**

This type connects to external processes that provide tools using the Model Context Protocol (MCP). `yacba` distinguishes between `stdio` and `http` transports based on the presence of `command` or `url`.

**Example `aws-cli-stdio.tools.json` (stdio transport):**
```json
{
  "id": "awslabs.aws-api-mcp-server",
  "type": "mcp",
  "command": "uvx",
  "args": [
    "-q",
    "awslabs.aws-api-mcp-server@latest"
  ]
}
```

**Example `some-service-http.tools.json` (http transport):**
```json
{
  "id": "some-remote-service",
  "type": "mcp",
  "url": "http://localhost:8080/mcp"
}
```

### **Type 2: Python Modules (`type: "python"`)**

This type loads tools directly from functions in a local Python file. The functions must be valid strands tools (e.g., decorated with `@tool`). The `module_path` is relative to the location of the `.tools.json` file.

**Example `local-files.tools.json`:**
```json
{
  "id": "local-file-lister",
  "type": "python",
  "module_path": "../sample-python-tools/local_tools.py",
  "functions": [
    "list_files"
  ]
}
```

## **Advanced Examples**

### **Code Analysis with a Custom Tool**

Analyze a Python project directory using a custom tool for listing files, running on a local `ollama` model, and saving the session.

```bash
./yacba \
  -m litellm:ollama/llama3 \
  -p "You are a senior software engineer. Analyze the following codebase and suggest improvements." \
  -f "/path/to/my/project[*.py]" \
  -t "/path/to/my/tools" \
  --session-name "code-review-llama3"
```

### **Headless Scripting with AWS Tools**

Use headless mode to ask the AWS CLI tool to list S3 buckets and pipe the output to a file.

```bash
./yacba --headless \
  -m bedrock:anthropic.claude-3-sonnet-20240229-v1:0 \
  -t "/path/to/aws/tool/config" \
  -i "Using my tools, list all of my S3 buckets in the us-east-1 region." > s3_buckets.txt
```
