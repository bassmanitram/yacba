# YACBA - Yet Another ChatBot Agent

**Refactored Architecture (v2.0)** - A sophisticated chatbot framework built on specialized packages for maximum modularity and maintainability.

## 🏗️ Architecture Overview

YACBA has been completely refactored to leverage best-in-class specialized packages:

- **🧠 YACBA Core**: Configuration management, CLI parsing, and orchestration
- **🏭 [strands_agent_factory](https://github.com/bassmanitram/strands-agent-factory)**: Agent lifecycle, tool management, and AI provider integration
- **💬 [repl_toolkit](https://github.com/your-org/repl-toolkit)**: Interactive and headless user interfaces with prompt_toolkit

This separation of concerns provides:
- **Better Maintainability**: Each package handles its domain expertise
- **Enhanced Features**: Leverage specialized functionality from each package
- **Reduced Complexity**: Clean interfaces between components
- **Future-Proof Design**: Easy to upgrade individual components

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/yacba.git
cd yacba/code

# Install dependencies (including strands_agent_factory and repl_toolkit)
pip install -r requirements.txt

# Basic usage
python yacba_new.py --help
```

### Basic Examples

```bash
# Interactive mode (default)
python yacba_new.py --model "gpt-4o"

# Headless mode for scripting  
python yacba_new.py --headless --initial-message "Analyze the current directory"

# With tools and files
python yacba_new.py --tool-configs-dir ./tools --files "*.py" "text/plain"

# Custom conversation management
python yacba_new.py --conversation-manager sliding_window --window-size 50
```

## 🎯 Key Features

### Comprehensive AI Provider Support
- **OpenAI**: GPT-4, GPT-4o, GPT-3.5 models
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus/Haiku  
- **Google**: Gemini 2.5 Flash, Gemini Pro via LiteLLM
- **Local Models**: Ollama integration for privacy
- **AWS Bedrock**: Enterprise-grade deployment
- **100+ Providers**: Via LiteLLM integration

### Advanced Tool System
- **Python Functions**: Load any Python function as a tool
- **MCP Servers**: Model Context Protocol server integration
- **Automatic Discovery**: Scan directories for tool configurations
- **Dynamic Loading**: Hot-reload tools without restart
- **Schema Adaptation**: Automatic tool schema conversion for different AI providers

### Intelligent Conversation Management
- **Sliding Window**: Keep recent messages, forget old ones
- **Summarizing**: AI-powered summarization of conversation history
- **Null Manager**: Disable management for unlimited context
- **Configurable Thresholds**: Fine-tune memory management

### Rich Interactive Experience
- **Prompt Toolkit**: Full-featured readline with history, completion
- **Command System**: Built-in `/` commands for session management
- **Cancellation Support**: Cancel long-running operations with Alt+C
- **Multi-line Input**: Alt+Enter to send, Enter for new line
- **Tab Completion**: Context-aware completion for commands and inputs

### Session Persistence
- **Named Sessions**: Resume conversations by name
- **File-based Storage**: Persistent conversation history
- **Agent Identity**: Custom agent IDs for multi-agent workflows
- **History Management**: Configurable history retention

### File Processing
- **Multi-format Support**: PDF, DOC, CSV, JSON, Markdown, images
- **Batch Upload**: Upload multiple files simultaneously  
- **Smart Content Extraction**: Automatic content parsing and preparation
- **Mimetype Detection**: Automatic or manual mimetype specification

## 📋 Command Line Interface

YACBA provides a comprehensive CLI with over 20 options for complete customization:

### Core Configuration
```bash
python yacba_new.py [OPTIONS]

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
  --config FILE                   Configuration file path
  --list-profiles                 Show available profiles
  --show-config                   Display resolved configuration
  --init-config PATH              Create sample configuration file

Performance:
  --clear-cache                   Clear performance cache before starting
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

Usage: `python yacba_new.py --profile development`

## 🛠️ Tool Configuration

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
python yacba_new.py --tool-configs-dir ./tools/
```

YACBA will automatically discover and load all `*.json` and `*.yaml` files in the directory.

## 🎨 User Interface Customization

### Interactive Mode Customization
```bash
# Custom prompts with HTML formatting
python yacba_new.py \
  --cli-prompt "<b><blue>🤖 User:</blue></b> " \
  --response-prefix "<b><green>🤖 Assistant:</green></b> "

# Tool usage visibility
python yacba_new.py --show-tool-use
```

### Built-in Commands
In interactive mode, use these commands:

- `/help` - Show available commands
- `/clear` - Clear conversation history
- `/info` - Show current session information
- `/session save <name>` - Save current session
- `/session load <name>` - Load saved session
- `/tools` - List available tools
- `/quit`, `/exit` - Exit the application

## 🔧 Architecture Details

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

The refactored architecture uses adapters to bridge between different packages:

1. **YacbaToStrandsConfigConverter**: Converts YACBA's rich configuration to strands_agent_factory format
2. **YacbaStrandsBackend**: Implements repl_toolkit protocols using strands_agent_factory agents
3. **YacbaCommandAdapter**: Bridges YACBA's command system with repl_toolkit's command handler
4. **YacbaCompleterAdapter**: Adapts YACBA's completion system to repl_toolkit's completer protocol

## 📊 Performance & Scalability

### Memory Management
- **Conversation Strategies**: Automatic context window management
- **Tool Result Caching**: Intelligent caching of expensive tool operations
- **Session Persistence**: Efficient storage of conversation state

### Best Practices
- Use sliding window for long conversations
- Choose appropriate models for different tasks (GPT-4 for reasoning, GPT-4-mini for simple tasks)
- Configure session persistence for multi-turn workflows
- Use MCP servers for external system integration

## 🔍 Debugging & Troubleshooting

### Logging Configuration
```bash
# Enable debug logging
export LOGURU_LEVEL=DEBUG
python yacba_new.py --model "gpt-4o"

# Enable trace-level for detailed debugging  
export LOGURU_LEVEL=TRACE
python yacba_new.py --show-config
```

### Common Issues

1. **Module Import Errors**: Ensure strands_agent_factory and repl_toolkit are in Python path
2. **API Credentials**: Set appropriate environment variables (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
3. **Tool Loading Failures**: Check tool configuration syntax and file paths
4. **Memory Issues**: Adjust conversation manager settings for large contexts

### Configuration Validation
```bash
# Validate configuration without starting agent
python yacba_new.py --show-config

# Test specific profile
python yacba_new.py --profile development --show-config

# Initialize sample configuration
python yacba_new.py --init-config ~/.yacba/sample-config.yaml
```

## 🚦 Migration from Legacy YACBA

The refactored YACBA maintains full backward compatibility:

### Command Line Arguments
✅ **All existing arguments preserved**  
✅ **Same behavior and semantics**  
✅ **Configuration files unchanged**  

### Breaking Changes
❌ **None** - Complete backward compatibility maintained

### Migration Steps
1. Update dependencies: `pip install -r requirements.txt`
2. Replace `python yacba.py` with `python yacba_new.py`
3. All existing scripts and configurations continue to work unchanged

## 🔮 Future Roadmap

- **Plugin System**: Dynamic plugin loading for custom adapters
- **Web Interface**: Browser-based interface option
- **Multi-Agent Orchestration**: Coordinate multiple AI agents
- **Advanced Tool Authoring**: Visual tool creation interface
- **Cloud Deployment**: Containerized deployment options
- **Performance Analytics**: Detailed usage and performance metrics

## 🤝 Contributing

We welcome contributions! The modular architecture makes it easy to contribute to specific areas:

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
- **Separation of Concerns**: Each package handles its domain
- **Protocol-Based Design**: Use protocols for loose coupling
- **Backward Compatibility**: Never break existing functionality
- **Comprehensive Testing**: All changes must include tests

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[strands-agents](https://github.com/pydantic/strands-agents)**: Core AI agent framework
- **[strands_agent_factory](https://github.com/bassmanitram/strands-agent-factory)**: Agent lifecycle management
- **[repl_toolkit](https://github.com/your-org/repl-toolkit)**: Interactive interface framework
- **[prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit)**: Rich terminal interfaces
- **All contributors**: Making YACBA better with each release

---

**YACBA v2.0** - Modular • Powerful • Developer-Friendly