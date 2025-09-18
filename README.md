# **Yet Another ChatBot Agent (yacba)**

Yacba provides a flexible and configurable command-line AI agent powered by the **strands-agents** library. It can be run as an interactive, multi-turn chatbot with advanced features like file uploads and tool integration, or as a non-interactive "headless" agent for use in command pipelines and scripts.

## **Features**

* **Dual Modes:** Seamlessly switch between an interactive chatbot experience and a non-interactive headless mode for scripting and automation.  
* **Multi-Framework Model Support:** Connect to any model framework supported by strands-agents, including litellm, openai, anthropic, and bedrock.  
* **Extensible Tool Integration:** Dynamically load tools for the agent from various sources:  
  * **External MCP Servers:** Connect to tools provided by local or remote Model Context Protocol (MCP) servers.  
  * **Local Python Modules:** Integrate your own Python functions decorated with @tool.  
  * **Pre-built Strands Tools:** Easily expose tools provided by the strands-agents library itself, such as the shell tool.  
* **Advanced File Handling:**  
  * **Startup Uploads:** Upload multiple files or entire directories at startup using the `-f` flag.  
    * Recursively scans directories with optional glob filters (e.g., `-f my_dir[*.py,*.js]`).  
    * Supports overriding the detected mimetype for uploaded files.  
    * Configurable `--max-files` limit.  
  * **In-Chat Uploads:** Upload files during a conversation using the `file('path/to/file')` syntax. This also supports uploading entire directories and using glob filters, just like the `-f` flag (e.g., `file('my_dir[*.py,*.js]')`).  
* **Rich CLI Experience:**  
  * **Persistent Command History:** Navigate previous inputs with arrow keys.  
  * **Real-time Streaming Responses:** Receive model responses as they are generated.  
  * **Interactive Path Auto-completion:** Press Tab for path suggestions when typing `file('` in chat.  
  * **Interactive Meta-Commands:** Control the application with commands like `/save`, `/clear`, `/history`, `/tools`, and `/help`.  
  * **Robust Error Handling:** Catches and details model provider API errors, and ensures non-zero exit codes on failure in headless mode.  
* **Highly Configurable:**  
  * Customize the agent's behavior with system prompts (string or loaded from a `file://` URI).  
  * Use the `-l/--legacy-prompt` flag for models that don't support system prompts natively.  
  * Specify different models and provide model-specific configurations via `--model-config` JSON files or individual `-c KEY:VALUE` flags.  
* **Conversation Persistence:**  
  * Save and load conversation history using the `--session-name` flag, allowing you to resume sessions later.

## **Installation**

1. **Clone the repository (or download the source files).**  
2. Change to the code directory:
  ```
   cd yacba/code  
  ```
3. Create and activate a Python virtual environment (recommended):  
  ```
   python -m venv .venv  
   source .venv/bin/activate  
  ```
4. Install the required dependencies:  
  ```
   pip install -r requirements.txt  
  ```
5. **Set up your environment variables.** You will need to configure API keys for your chosen model framework (e.g., `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) and/or set up your AWS credentials for Bedrock.

## **How to Run**

The main entry point for the application is `yacba.py`. A convenience shell script, `yacba`, is also provided.

### **Using the yacba Shell Script**

The yacba script is the recommended way to run the application. It automatically finds the `yacba.py` script, ensuring it can be run from any directory. It also suppresses common, noisy warnings from the underlying litellm library.

**To make it executable:**
  ```
  chmod +x yacba
  ```

**Example Usage:**

  ```
  ./yacba -m litellm:gemini/gemini-1.5-flash -t ../sample-tool-configs
  ```

### **Making yacba available everywhere (Optional)**

For easier access, you can create a symbolic link to the yacba script in a directory that is in your system's `PATH`. This will allow you to run yacba from any location without having to specify the path to the script.

**Example for Linux or macOS:**

  ```
  # Make sure the target directory (e.g., /usr/local/bin) exists and is in your PATH 
  sudo ln -s /path/to/your/yacba/code/yacba /usr/local/bin/yacba  
  ```
After creating the link, you can simply run `yacba` from any terminal.

### **Interactive Chatbot Mode**

To start a standard interactive chat session:

  ```
  ./yacba
  ```
You can exit the chat by typing `/exit` or `/quit`, or by pressing `Ctrl+C` or `Ctrl+D`. `Alt+Enter` will add a new line within your input. For a list of in-chat commands, type `/help`.

**Example with options (including legacy prompt mode):**

  ```
  ./yacba   
    -m bedrock:anthropic.claude-v2 \
    -p "You are an expert in AWS services." \
    -l \
    -f /path/to/my/project[*.tf,*.json] \
    -t ../sample-tool-configs \
    -c temperature:0.1
  ```

### **Interactive Meta-Commands**

While in an interactive session, you can use the following commands to control the application:

| Command | Description |
| :---- | :---- |
| `/help` | Show the list of available meta-commands. |
| `/save [name]` | Manually saves the current session. If `name` is provided, it sets or changes the session name before saving. |
| `/clear` | Clear the agent's current conversation history and start fresh. |
| `/history` | Print the current conversation history as a JSON object. |
| `/tools` | List the names of all tools currently available to the agent. |
| `/exit`, `/quit` | Exit the application. |

### **Headless Mode**

Headless mode is designed for scripting. It takes an initial message, streams the agent's response directly to stdout, and then exits with a 0 status code on success or 1 on failure.

**Using the -i flag:**

  ```
  ./yacba --headless -i "Summarize the main points of Moby Dick."
  ```

**Piping from stdin:**

  ```
  cat report.txt | ./yacba --headless
  ```

## **Configuring Tools**

You can extend the agent's capabilities by connecting it to tools from different sources. The application automatically discovers and loads tools at startup from `.tools.json` files found in the directory specified by the `-t/--tools` flag.

### **Type 1: MCP Servers (type: "mcp")**

This type connects to external processes that provide tools using the Model Context Protocol (MCP).

**Example aws-cli.tools.json:**

  ```
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
### **Type 2: Python Modules (type: "python")**

This type loads tools directly from functions or objects in a local Python file. The objects must be valid strands tools (e.g., decorated with @tool).

**Example local-files.tools.json:**

  ```
  {  
    "id": "local-file-lister",  
    "type": "python",  
    "module_path": "../sample-python-tools/local_tools.py",  
    "functions": [  
      "list_files"  
    ]  
  }
  ```

## **Command-Line Options**

| Flag | Description |
| :---- | :---- |
|`-c`, `--config-val` | Set a single model configuration value (e.g.,`-c temperature:0.8`). Overrides values from `--model-config`. |
|`-f`, `--file` | Uploads a file or a directory. Can be used multiple times. <br/>Syntax: `-f PATH [MIMETYPE]` or, for directories, `-f my_dir[*.py,*.js]` scans with glob filters. |
| `--headless` | Activates non-interactive headless mode. |
|`-i`, `--initial-message` | An initial message to send to the agent. In headless mode, if this is omitted, the message is read from stdin. |
|`-l`, `--legacy-prompt` | Use legacy mode for system prompts by injecting it into the first user message. For models that do not support native system prompts. |
| `--max-files` | Maximum number of files to upload via the`-f` flag. Default: 20. |
|`-m`, `--model` | Specifies the model to use in `framework:model_id` format (e.g., `openai:gpt-4o`, `bedrock:amazon.titan-text-express-v1`). If the framework is omitted, it will be guessed. |
| `--model-config` | Path to a JSON file with ad-hoc configuration for the model (e.g., `temperature`, `max_tokens`). |
|`-p`, `--prompt` | Sets the system prompt for the agent. Can be a string or a file URI (e.g., `file:///path/to/prompt.txt`). |
| `--session-name` | Load a session history and save it on exit. Filename is `<name>.yacba-session.json` in the CWD. |
|`-t`, `--tools` | Specifies the directory to load tool configurations (`*.tools.json`) from. <br/>- Defaults to the current directory (.). <br/>- If specified without a path, disables tool discovery. |

