# **Yet Another ChatBot Agent (yacba)**

Yacba provides a flexible and configurable command-line AI agent powered by the **strands-agents** library and **litellm**. It can be run as an interactive, multi-turn chatbot with advanced features like file uploads and tool integration, or as a non-interactive "headless" agent for use in command pipelines and scripts.

## **Features**

*   **Dual Modes:** Seamlessly switch between an interactive chatbot experience and a non-interactive headless mode for scripting and automation.
*   **Model Agnostic (via LiteLLM):** Connect to any language model supported by LiteLLM (e.g., Gemini, OpenAI, Anthropic, Cohere, etc.). The default model is `litellm:gemini/gemini-2.5-flash`.
*   **Extensible Tool Integration:** Dynamically load tools for the agent from various sources:
    *   **External MCP Servers:** Connect to tools provided by local or remote Model Context Protocol (MCP) servers.
    *   **Local Python Modules:** Integrate Python functions decorated with `@tool` from `strands-agents` directly.
    *   Tools are initialized in parallel for faster startup.
*   **Advanced File Handling:**
    *   **Startup Uploads:** Upload multiple files or entire directories at startup using the `-f` flag.
        *   Recursively scans directories for likely text files, with optional glob `filters` (e.g., `-f my_dir[*.py,*.js]`).
        *   Supports overriding the detected mimetype for uploaded files.
        *   Configurable `max-files` limit.
    *   **In-Chat Uploads:** Upload files during a conversation using the `file('path/to/file')` syntax.
    *   **Automatic Detection:** Intelligent text-file detection and mimetype guessing. Binary files are base64 encoded and sent using a generic `image` content type (as handled by `strands-agents`).
*   **Rich CLI Experience:**
    *   **Persistent Command History:** Navigate previous inputs with arrow keys.
    *   **Real-time Streaming Responses:** Receive model responses as they are generated.
    *   **Interactive Path Auto-completion:** Press `Tab` for path suggestions when typing `file('` in chat.
    *   **Intelligent Tool Output:** Suppresses verbose internal tool usage logs for cleaner output.
    *   **Robust Error Handling:** Catches and details `litellm` API connection and service unavailability errors.
*   **Highly Configurable:**
    *   Customize the agent's behavior with system prompts (string or loaded from a `file://` URI).
    *   Specify different models and provide model-specific configurations via `--model-config` JSON files or individual `-c KEY:VALUE` flags.
    *   Control tool discovery behavior (enable/disable) via the `-t/--tools` flag.

## **Installation**

1.  **Clone the repository (or download the source files).**
2.  **Change to the code directory:**

    ```bash
    cd yacba/code
    ```

3.  **Create and activate a Python virtual environment (recommended):**

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

4.  **Install the required dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

5.  **Set up your environment variables.** For many models (like Gemini, OpenAI), you will need to configure API keys for litellm to use. Please refer to the [LiteLLM documentation](https://docs.litellm.ai/docs/providers) for provider-specific setup.

## **How to Run**

The main entry point for the application is `yacba.py`.

### **Interactive Chatbot Mode**

To start a standard interactive chat session, simply run the script:

```bash
python yacba.py
```

You can exit the chat by typing `exit` or `quit`, or by pressing `Ctrl+C` or `Ctrl+D`. `Alt+Enter` will add a new line within your input.

**Example with options:**

```bash
python yacba.py \
  -m litellm:gemini/gemini-1.5-flash \
  -p "file:///path/to/my/expert_prompt.txt" \
  -f /path/to/my/data.csv text/csv \
  -f /path/to/my/project_docs[*.md,*.txt] \
  -t ../sample-tool-configs \
  -c temperature:0.7 \
  --model-config my_model_settings.json
```

### **Headless Mode**

Headless mode is designed for scripting. It takes an initial message, streams the agent's response directly to stdout, and then exits. All status messages and errors are printed to stderr.

**Using the -i flag:**

```bash
python yacba.py --headless -i "Summarize the main points of Moby Dick."
```

**Piping from stdin:**

```bash
cat report.txt | python yacba.py --headless
```

## **Configuring Tools**

You can extend the agent's capabilities by connecting it to tools from different sources. The application automatically discovers and loads tools at startup from `.tools.json` files found in the directory specified by the `-t/--tools` flag (which defaults to the current directory).

To disable tool discovery, simply use the `-t` flag without providing a path: `python yacba.py -t`

Each `.tools.json` file defines one or more tools and includes a `type` field to specify the source and connection method.

### **Type 1: MCP Servers (`type: "mcp"`)**

This type connects to external processes that provide tools using the Model Context Protocol (MCP). Two connection methods are supported:

*   **`command` (stdio):** The application will start a local process and communicate with it over standard input/output.
*   **`url` (http):** The application will connect to a remote MCP server that is already running at the specified HTTP address.

**Example `aws-cli.tools.json` (starts a local process):**

```json
{
  "id": "awslabs.aws-api-mcp-server",
  "type": "mcp",
  "command": "uvx",
  "args": [
    "-q",
    "awslabs.aws-api-mcp-server@latest"
  ],
  "disabled": false
}
```

**Example `remote-tool-server.tools.json` (connects to a running HTTP server):**

```json
{
  "id": "my-remote-server",
  "type": "mcp",
  "url": "http://localhost:8000/mcp",
  "disabled": false
}
```

*   **`id`**: A unique identifier for the MCP server.
*   **`type`**: Must be `"mcp"`.
*   **`command`**: (Optional) The executable command to start the MCP server process. Used with `args`.
*   **`args`**: (Optional) A list of command-line arguments for the `command`.
*   **`url`**: (Optional) The HTTP address of a running remote MCP server.
*   **`env`**: (Optional) A dictionary of environment variables to set for the `command` process.
*   **`disabled`**: (Optional, boolean) If `true`, this tool configuration will be ignored. Defaults to `false`.

### **Type 2: Python Modules (`type: "python"`)**

This type loads tools directly from functions within a local Python file. The functions must be decorated with `@tool` from the `strands-agents` library.

**Example `local-files.tools.json`:**

```json
{
  "id": "local-file-lister",
  "type": "python",
  "module_path": "../sample-python-tools/local_tools.py",
  "functions": ["list_files"],
  "disabled": false
}
```

*   **`id`**: A unique identifier for this tool set.
*   **`type`**: Must be `"python"`.
*   **`module_path`**: The path to the Python file, absolute or relative to the location of the `.tools.json` file.
*   **`functions`**: A list of the function names to load from the module. Only functions decorated with `@tool` will be loaded.
*   **`disabled`**: (Optional, boolean) If `true`, this tool configuration will be ignored. Defaults to `false`.

## **Command-Line Options**

| Flag                   | Description                                                                                                                                                                                                                                                            |
| :--------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `-p, --prompt`         | Sets the system prompt for the agent. Can be a string or a file URI (e.g., `file:///path/to/prompt.txt`). Default: A general assistant prompt.                                                                                                                         |
| `-m, --model`          | Specifies the LiteLLM model ID to use (e.g., `litellm:gemini/gemini-1.5-flash`, `litellm:gpt-4o`). Default: `litellm:gemini/gemini-2.5-flash`.                                                                                                                        |
| `-f, --file`           | Uploads a file or a directory at startup. Can be used multiple times. <br/>Syntax: `-f PATH [MIMETYPE]` <br/>- `PATH`: File or directory path. <br/>- `MIMETYPE`: (Optional) Overrides guessed mimetype. <br/>- For directories: `my_dir[*.py,*.js]` scans with glob filters. |
| `--max-files`          | Maximum number of files to upload via the `-f` flag. Default: `20`.                                                                                                                                                                                                    |
| `-t, --tools`          | Specifies the directory to load tool configurations (`*.tools.json`) from. <br/>- Defaults to the current directory (`.`). <br/>- If specified **without** a path (e.g., `-t`), it disables tool discovery.                                                             |
| `-i, --initial-message`| An initial message to send to the agent. In headless mode, if this is omitted, the message is read from stdin.                                                                                                                                                         |
| `--headless`           | Activates non-interactive headless mode. Reads a message, prints the response to stdout, and exits. Status messages go to stderr.                                                                                                                                       |
| `--model-config`       | Path to a JSON file with ad-hoc configuration for the LiteLLM model (e.g., `temperature`, `max_tokens`). Values here can be overridden by `-c` flags.                                                                                                                  |
| `-c, --config-val`     | Set a single model configuration value (e.g., `-c temperature:0.8`, `-c max_tokens:1000`, `-c streaming:false`). Can be used multiple times. Overrides values from `--model-config`.                                                                                  |
