# YACBA Documentation

Welcome to the YACBA (Yet Another ChatBot Agent) documentation.

YACBA is built on [strands-agent-factory](https://github.com/bassmanitram/strands-agent-factory). For core agent concepts, tool development, and advanced features, refer to the [strands-agent-factory documentation](https://github.com/bassmanitram/strands-agent-factory#readme).

## Documentation Files

This directory contains documentation for YACBA's CLI wrapper layer - configuration, interactive interface, and integration with strands-agent-factory.

**[ARCHITECTURE.md](ARCHITECTURE.md)** - System design  
How YACBA wraps strands-agent-factory, component diagrams, data flow, and design patterns.

**[API.md](API.md)** - API reference  
Configuration system (YacbaConfig), adapters, utilities, and type definitions.

**[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Problem solving  
Quick diagnostics, common issues, configuration problems, and debugging techniques.

### External Resources

- **[Main README](../README.md)** - Getting started, usage examples, configuration
- **[strands-agent-factory](https://github.com/bassmanitram/strands-agent-factory)** - Core agent features and tool development  
- **[profile-config](https://pypi.org/project/profile-config/)** - Profile system documentation
- **[repl-toolkit](https://pypi.org/project/repl-toolkit/)** - Interactive REPL framework
- **[dataclass-args](https://pypi.org/project/dataclass-args/)** - CLI argument generation

---

## What's Documented Where

### YACBA Documentation (This Directory)

Covers the CLI wrapper:
- Command-line argument parsing
- Configuration profiles and precedence
- Interactive REPL with tab completion
- Headless mode for automation
- Configuration conversion for strands-agent-factory
- File management and glob processing

### strands-agent-factory Documentation

Covers core agent functionality:
- LLM provider integration (OpenAI, Anthropic, AWS Bedrock, etc.)
- Tool system (Python functions, MCP servers, A2A agents)
- Conversation management strategies
- Session persistence
- Agent lifecycle
- Tool development guides

For most agent-related questions, see [strands-agent-factory docs](https://github.com/bassmanitram/strands-agent-factory#readme).

---

## Quick Links

### Getting Started

- [Installation](../README.md#getting-started)
- [Basic Usage](../README.md#usage)
- [Configuration Files](../README.md#configuration-files)
- [Interactive Mode](../README.md#interactive-mode)

### Configuration

- [CLI Options](../README.md#usage) - Command-line arguments
- [Configuration Precedence](ARCHITECTURE.md#configuration-flow) - How settings are merged
- [Profile System](../README.md#configuration-files) - Named configuration sets
- [YacbaConfig API](API.md#yacbaconfig) - Configuration dataclass reference

### Tool Configuration

- [Tool Examples](../README.md#tools) - Python, MCP, and A2A tools
- [Sample Configs](../code/sample-tool-configs/) - Working examples
- [Tool Development](https://github.com/bassmanitram/strands-agent-factory#tools) - Creating custom tools

### Architecture

- [System Design](ARCHITECTURE.md) - How YACBA is structured
- [Component Diagrams](ARCHITECTURE.md#component-diagrams) - Visual architecture
- [Data Flow](ARCHITECTURE.md#data-flow) - How information moves through the system
- [Extension Points](ARCHITECTURE.md#extension-points) - How to extend YACBA

### Troubleshooting

- [Quick Diagnostics](TROUBLESHOOTING.md#quick-diagnostics) - Fast problem identification
- [Common Issues](TROUBLESHOOTING.md#common-issues) - Frequently encountered problems
- [Debug Logging](TROUBLESHOOTING.md#enable-debug-logging) - Verbose output for troubleshooting
- [Session Repair](../README.md#corrupted-sessions) - Fix corrupted sessions

---

## Interactive Features

### Commands

When running interactively, these commands are available:

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

### Keyboard Shortcuts

- **Alt+Enter** - Submit your message
- **Alt+C** - Cancel running operation
- **Ctrl+C** - Cancel or exit
- **Ctrl+R** - Search history
- **F6** - Paste from clipboard
- **Escape+!** - Enter a shell command (type `sh` to drop into a shell session)

### Tab Completion

The REPL provides intelligent completion for:
- Commands (`/h<Tab>` → `/help`, `/history`)
- File paths (`file("/tmp/<Tab>` → directory contents)
- Shell variables (`${HOME}<Tab>` → `/home/username`)
- Shell commands (`$(whoami)<Tab>` → username)

See the [main README](../README.md#tab-completion-examples) for more examples.

---

## Configuration System

YACBA merges configuration from multiple sources in this order (highest priority first):

1. Command-line arguments
2. Config file specified with `--config-file`
3. Discovered config files (`~/.yacba/config.yaml`, `./.yacba/config.yaml`)
4. Environment variables (`YACBA_*`)
5. Default values

Configuration files support profiles - named sets of options you can switch between. See the [profile-config documentation](https://pypi.org/project/profile-config/) for advanced features like profile inheritance and variable substitution.

---

## Common Tasks

### View Configuration

```bash
# Show resolved configuration
python code/yacba.py --show-config

# List available profiles
python code/yacba.py --list-profiles
```

### Enable Debug Logging

```bash
export YACBA_LOG_LEVEL=DEBUG
python code/yacba.py
```

### Repair Corrupted Sessions

If a session fails to load due to interrupted tool execution:

```bash
python code/scripts/fix_strands_session.py ~/.yacba/sessions/session_name

# Preview changes first
python code/scripts/fix_strands_session.py --dry-run ~/.yacba/sessions/session_name
```

See [Corrupted Sessions](../README.md#corrupted-sessions) in the main README for details.

---

## API Reference Quick Links

### Configuration

- [YacbaConfig](API.md#yacbaconfig) - Main configuration dataclass
- [parse_config()](API.md#parse_config) - Configuration parser

### Adapters

- [YacbaToStrandsConfigConverter](API.md#yacbatostrandsconfigconverter) - Config conversion
- [YacbaBackend](API.md#yacbabackend) - Backend implementation

### Utilities

- [discover_tool_configs()](API.md#discover_tool_configs) - Tool config discovery
- [ModelConfigParser](API.md#modelconfigparser) - Model config parsing

---

## Architecture Quick Links

- [System Context](ARCHITECTURE.md#high-level-architecture) - YACBA's relationship to strands-agent-factory
- [Component Interaction](ARCHITECTURE.md#component-interaction-flow) - How components work together
- [Configuration Flow](ARCHITECTURE.md#configuration-flow) - Config precedence and loading
- [Message Flow](ARCHITECTURE.md#message-flow-interactive-mode) - Message handling
- [Design Patterns](ARCHITECTURE.md#design-patterns) - Adapter pattern, protocols
- [Extension Points](ARCHITECTURE.md#extension-points) - How to extend YACBA

---

## Troubleshooting Quick Links

- [Quick Diagnostics](TROUBLESHOOTING.md#quick-diagnostics) - Fast problem identification
- [Common Issues](TROUBLESHOOTING.md#common-issues) - Frequently encountered problems
- [Configuration Problems](TROUBLESHOOTING.md#configuration-problems) - Config issues
- [Tool Loading Issues](TROUBLESHOOTING.md#tool-loading-issues) - Tool configuration errors
- [Session Repair](TROUBLESHOOTING.md#session-corruption) - Fix corrupted sessions

---

## Contributing to Documentation

When updating documentation:

1. **Distinguish scope** - YACBA docs cover the wrapper; link to strands-agent-factory for core features
2. **Update all references** - If you change something, check all doc files
3. **Include examples** - Show working code where possible
4. **Cross-reference** - Link between docs appropriately
5. **Update dates** - Change "Last Updated" dates when making changes

---

## Version Information

- **YACBA Version**: 2.0+
- **strands-agent-factory**: 1.1.1+
- **repl-toolkit**: 1.2.0+
- **dataclass-args**: 1.1.0+
- **profile-config**: 1.0.0+
- **Documentation Version**: 2.0
- **Last Updated**: 2025-01-15

---

## License

This documentation is part of the YACBA project and is licensed under the MIT License.
