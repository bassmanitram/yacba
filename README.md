# **Yet Another ChatBot Agent (yacba)**

Yacba provides a flexible and configurable command-line AI agent powered by the **strands-agents** library and **litellm**. It can be run as an interactive, multi-turn chatbot with advanced features like file uploads and tool integration, or as a non-interactive "headless" agent for use in command pipelines and scripts.

## **Features**

* **Dual Modes:** Run as an interactive chatbot or as a headless agent for scripting.  
* **Model Agnostic:** Connect to any language model supported by litellm (e.g., Gemini, OpenAI, Anthropic models).  
* **Extensible Tool Integration:** Dynamically load tools for the agent from external MCP servers or local Python modules. Configure tools via simple JSON files to add new capabilities.  
* **Advanced File Handling:**  
  * Upload multiple files or entire directories at startup.  
  * Upload files during a conversation with file('path/to/file').  
  * Automatic text-file detection and mimetype guessing.  
* **Rich CLI Experience:**  
  * Persistent command history (use arrow keys to navigate).  
  * Real-time, streaming responses from the model.  
  * Interactive path auto-completion when uploading files.  
* **Configurable:** Customize the agent's behavior with system prompts, different models, and various command-line flags.

## **Installation**

1. **Clone the repository (or download the source files).**  
2. **Change to the code directory:**

  ```
   cd yacba/code
  ```
3. **Create and activate a Python virtual environment (recommended):**  
  ```
   python -m venv .venv  
   source .venv/bin/activate
  ```

4. **Install the required dependencies:**  
  ```
   pip install -r requirements.txt
  ```

5. **Set up your environment variables.** For many models (like Gemini), you will need to configure API keys for litellm to use. Please refer to the [LiteLLM documentation](https://docs.litellm.ai/docs/providers) for provider-specific setup.

## **How to Run**

The main entry point for the application is `yacba.py`, but there is a BASH script that slightly simplifies the startup: `yacba`

### **Interactive Chatbot Mode**

To start a standard interactive chat session, simply run the script:

```
python yacba.py
```

You can exit the chat by typing `exit` or `quit`, or by pressing `Ctrl+C` or `Ctrl+D`.

**Example with options:**

```
python yacba.py \  
  -m gemini/gemini-pro \  
  -p "You are a helpful assistant that analyzes CSV files." \  
  -f /path/to/my/data.csv \  
  -t ../sample-tool-configs
```

### **Headless Mode**

Headless mode is designed for scripting. It takes an initial message, streams the agent's response directly to stdout, and then exits. All status messages are printed to stderr.

**Using the -i flag:**

```
python yacba.py --headless -i "Summarize the main points of Moby Dick."
```

**Piping from stdin:**

```
cat report.txt | python yacba.py --headless
```

## **Configuring Tools**

You can extend the agent's capabilities by connecting it to tools from different sources. The application automatically discovers and loads tools at startup.

To configure a tool, create a JSON file with the `.tools.json` extension in the directory specified by the `-t/--tools` flag (which defaults to the current directory).

Each `.tools.json` file defines one or more tools and includes a type field to specify the source.

### **Type 1: MCP Servers**

This type connects to external processes that provide tools using the Model Context Protocol (MCP). Two connection methods are supported:

* **stdio:** The application will start a local process and communicate with it over standard input/output.  
* **url:** The application will connect to a remote MCP server that is already running at the specified HTTP address.

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

### **Type 2: Python Modules**

This type loads tools directly from functions in a local Python file. The functions must be decorated with `@tool` from the strands-agents library.

**Example local-files.tools.json:**

```
{  
  "id": "local-file-lister",  
  "type": "python",  
  "module_path": "../sample-python-tools/local_tools.py",  
  "functions": ["list_files"]  
}
```

* **module_path**: The path to the Python file, absolute or relative to the location of the `.tools.json` file.  
* **functions**: A list of the function names to load from the module.

## **Command-Line Options**

| Flag | Description |
| :---- | :---- |
| -p, --prompt | Sets the system prompt for the agent. Can be a string or a file URI (e.g., file:///path/to/prompt.txt). |
| -m, --model | Specifies the litellm model ID to use (e.g., gemini/gemini-1.5-flash, gpt-4o). |
| -f, --file | Uploads a file or a directory. Can be used multiple times. Recursively scans directories for text files. |
| -t, --tools | Specifies the directory to load tool configurations (\*.tools.json) from. Defaults to the current directory. If specified without a path, then the option disables tool discovery. |
| -i, --initial-message | An initial message to send to the agent. In headless mode, if this is omitted, the message is read from stdin. |
| --headless | Activates non-interactive headless mode. |

