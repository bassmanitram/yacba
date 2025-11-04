# YACBA Documentation

Welcome to the YACBA (Yet Another ChatBot Agent) documentation!

> **Note**: YACBA is built on [strands-agent-factory](https://github.com/JBarmentlo/strands-agent-factory).  
> For core agent concepts, tool development, and advanced features, refer to the  
> [strands-agent-factory documentation](https://github.com/JBarmentlo/strands-agent-factory#readme).

## Documentation Overview

This directory contains documentation for **YACBA's wrapper layer** - the CLI, configuration system, and REPL interface.

### Core Documentation

1. **[API Documentation](API.md)** - YACBA's wrapper APIs
   - Configuration system (YacbaConfig)
   - Adapters (YACBA ↔ strands-agent-factory)
   - Utilities (file loading, config discovery)
   - Type definitions

2. **[Architecture Documentation](ARCHITECTURE.md)** - System design
   - How YACBA wraps strands-agent-factory
   - Component diagrams
   - Data flow
   - Design patterns

3. **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Problem solving
   - Quick diagnostics
   - Common issues
   - Configuration problems
   - Debugging techniques

4. **[Completion System](COMPLETION_SYSTEM.md)** - Tab completion details
   - Architecture overview
   - Completion types (commands, files, shell)
   - Performance characteristics
   - Extensibility guide

### External Resources

- **[Main README](../README.md)** - Quick start and feature overview
- **[Configuration Guide](../README.CONFIG.md)** - Configuration system details (if exists)
- **[Model Configuration Guide](../README.MODEL_CONFIG.md)** - Model config parsing (if exists)
- **[strands-agent-factory Docs](https://github.com/JBarmentlo/strands-agent-factory#readme)** - Core agent features, tool development
- **[strands-agents Docs](https://github.com/pydantic/strands-agents)** - Underlying framework

---

## What's Documented Here vs strands-agent-factory

### YACBA Documentation (This Directory)

Covers **wrapper functionality**:
- CLI argument parsing via dataclass-args
- Configuration profiles via profile-config
- Interactive REPL via repl-toolkit
- Adapters that convert YACBA config → strands-agent-factory config
- File management and glob processing
- Headless mode automation

### strands-agent-factory Documentation

Covers **core agent functionality**:
- LLM provider integration (OpenAI, Anthropic, etc.)
- Tool system (Python, MCP, A2A)
- Conversation management strategies
- Session persistence
- Agent lifecycle
- Tool development guides

**For most agent-related questions**, see [strands-agent-factory docs](https://github.com/JBarmentlo/strands-agent-factory#readme) first.

---

## Quick Links

### Getting Started

- [Installation](../README.md#installation)
- [Quick Start](../README.md#quick-start)
- [Basic Examples](../README.md#examples)
- [When to use YACBA vs strands-agent-factory](../README.md#when-to-use-yacba-vs-strands-agent-factory-directly)

### Configuration

- [CLI Options](../README.md#cli-reference) - Auto-generated via dataclass-args
- [Configuration Precedence](ARCHITECTURE.md#configuration-precedence)
- [Profile System](../README.md#configuration-system)
- [YacbaConfig API](API.md#configuration-system)

### Tool Configuration

- [Tool Examples](../README.md#tool-configuration)
- [Sample Configs](../sample-tool-configs/) - Python, MCP, A2A examples
- [strands-agent-factory Tool Docs](https://github.com/JBarmentlo/strands-agent-factory#tools) - Tool development

### Development

- [Module Structure](ARCHITECTURE.md#module-structure)
- [Extension Points](ARCHITECTURE.md#extension-points)
- [Design Patterns](ARCHITECTURE.md#design-patterns)

### Troubleshooting

- [Quick Diagnostics](TROUBLESHOOTING.md#quick-diagnostics)
- [Common Issues](TROUBLESHOOTING.md#common-issues)
- [Debugging Techniques](TROUBLESHOOTING.md#debugging-techniques)

---

## Documentation Structure

```
docs/
├── README.md              # This file - documentation index
├── API.md                 # YACBA wrapper API reference
├── ARCHITECTURE.md        # System design and architecture
├── TROUBLESHOOTING.md     # Problem solving guide
└── COMPLETION_SYSTEM.md   # Tab completion system details
```

---

## Key Concepts

### YACBA's Role

YACBA is a **thin CLI wrapper** around strands-agent-factory that adds:

1. **CLI Interface** - Argument parsing via dataclass-args
2. **Configuration Management** - Profiles, discovery, precedence
3. **Interactive REPL** - Tab completion, history, commands
4. **Headless Mode** - Script-friendly automation
5. **File Management** - Glob patterns, MIME detection

All core agent functionality (LLM integration, tool execution, conversation management) comes from [strands-agent-factory](https://github.com/JBarmentlo/strands-agent-factory).

### Configuration System

YACBA uses a **5-level configuration precedence system**:

1. CLI arguments (highest)
2. User-specified config file
3. Discovered config files
4. Environment variables  
5. Default values (lowest)

See [Configuration System](ARCHITECTURE.md#configuration-system) for details.

### Adapter Pattern

YACBA uses **adapters** to bridge YACBA ↔ strands-agent-factory:

- **YacbaToStrandsConfigConverter** - Config conversion
- **YacbaBackend** - Backend protocol implementation  
- **YacbaCompleter** - Tab completion (file paths only)
- **YacbaActionRegistry** - Command system

Commands and shell expansion come from repl-toolkit.

See [Adapter Pattern](ARCHITECTURE.md#adapter-pattern-implementation) for details.

---

## Available Commands

YACBA provides these interactive commands (from repl-toolkit):

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/shortcuts` | Show keyboard shortcuts |
| `/status` | Show comprehensive session status |
| `/info`, `/stats` | Aliases for `/status` |
| `/tools` | List available tools |
| `/history` | Show conversation history |
| `/clear` | Clear conversation history |
| `/session save/load/list` | Session management |
| `/conversation-manager` | Change management strategy |
| `/conversation-stats` | Show statistics |
| `/shell` | Execute shell command |
| `/exit`, `/quit` | Exit application |

Commands have tab completion (alphabetically sorted).

---

## Common Tasks

### View Configuration

```bash
# Show resolved configuration
python code/yacba.py --show-config

# List available profiles
python code/yacba.py --list-profiles

# Initialize sample config
python code/yacba.py --init-config ~/.yacba/config.yaml
```

### Enable Debug Logging

```bash
# Debug level
export LOGURU_LEVEL=DEBUG
python code/yacba.py -m gpt-4o

# Trace level (very verbose)
export LOGURU_LEVEL=TRACE
python code/yacba.py -m gpt-4o
```

### Test Components

```python
# Test configuration parsing
PYTHONPATH=code python -c "
from config import parse_config
import sys
sys.argv = ['test', '-m', 'gpt-4o', '--show-config']
config = parse_config()
"

# Test adapter conversion
PYTHONPATH=code python -c "
from config import parse_config
from adapters.strands_factory import YacbaToStrandsConfigConverter
import sys
sys.argv = ['test', '-m', 'gpt-4o']
config = parse_config()
converter = YacbaToStrandsConfigConverter(config)
strands_config = converter.convert()
print('Conversion successful')
"
```

---

## API Reference Quick Links

### Configuration

- [YacbaConfig](API.md#yacbaconfig) - Main configuration dataclass
- [parse_config()](API.md#parse_config--yacbaconfig) - Configuration parser

### Adapters

- [YacbaToStrandsConfigConverter](API.md#yacbatostrandsconfigconverter) - Config conversion
- [YacbaBackend](API.md#yacbabackend) - Backend implementation
- [YacbaActionRegistry](API.md#yacbaactionregistry) - Command registry

### Utilities

- [discover_tool_configs()](API.md#discover_tool_configs) - Tool config discovery
- [ModelConfigParser](API.md#modelconfigparser) - Model config parsing

---

## Architecture Quick Links

### Diagrams

- [System Context](ARCHITECTURE.md#system-context) - YACBA's relationship to strands-agent-factory
- [Component Interaction](ARCHITECTURE.md#component-interaction-diagram) - How components work together
- [Configuration Flow](ARCHITECTURE.md#configuration-flow) - Config precedence and loading
- [Message Flow](ARCHITECTURE.md#message-flow-interactive-mode) - Message handling

### Design

- [Design Patterns](ARCHITECTURE.md#design-patterns) - Adapter, protocol-based design
- [Module Structure](ARCHITECTURE.md#module-structure) - Code organization
- [Extension Points](ARCHITECTURE.md#extension-points) - How to extend YACBA

---

## Troubleshooting Quick Links

### Diagnostics

- [Quick Diagnostics](TROUBLESHOOTING.md#quick-diagnostics) - Fast problem identification
- [Enable Debug Logging](TROUBLESHOOTING.md#enable-debug-logging) - Verbose output
- [Test Components](TROUBLESHOOTING.md#test-components-individually) - Isolate issues

### Common Issues

- [Module not found](TROUBLESHOOTING.md#issue-module-not-found-errors) - Import problems
- [API key errors](TROUBLESHOOTING.md#issue-api-key-not-found-errors) - Credential issues
- [Model errors](TROUBLESHOOTING.md#issue-model-not-found-or-invalid-model-errors) - Model string problems
- [Application hangs](TROUBLESHOOTING.md#issue-application-hangs-or-freezes) - Performance issues

### Specific Problems

- [Configuration Problems](TROUBLESHOOTING.md#configuration-problems) - Config loading/parsing
- [Tool Loading Issues](TROUBLESHOOTING.md#tool-loading-issues) - Tool configuration errors
- [Model Connection Problems](TROUBLESHOOTING.md#model-connection-problems) - Provider API issues
- [File Processing Issues](TROUBLESHOOTING.md#file-processing-issues) - File upload problems

---

## Contributing to Documentation

### Documentation Standards

1. **Clear Scope** - Distinguish YACBA docs from strands-agent-factory docs
2. **Link Appropriately** - Link to strands-agent-factory docs for core features
3. **Examples** - Provide working code examples
4. **Up-to-date** - Keep in sync with code

### Adding Documentation

1. **YACBA Features** - Update these docs
2. **Agent/Tool Features** - Link to strands-agent-factory docs
3. **New Issues** - Add to [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
4. **Update Index** - Update this README.md

### Documentation Format

- Use Markdown
- Include code examples  
- Add diagrams where helpful
- Cross-reference appropriately
- Link to strands-agent-factory docs for core features

---

## Version Information

- **YACBA Version**: 2.0+ (Wrapper Architecture)
- **strands-agent-factory Version**: 1.1.1+
- **repl-toolkit Version**: 1.2.0+
- **dataclass-args Version**: 1.1.0+
- **Documentation Version**: 2.0
- **Last Updated**: 2025-01-06

---

## Related Documentation

### Internal
- [Main README](../README.md) - User-facing documentation
- [Sample Configs](../sample-tool-configs/) - Tool configuration examples
- [Sample Model Configs](../sample-model-configs/) - Model parameter examples

### External
- **[strands-agent-factory](https://github.com/JBarmentlo/strands-agent-factory#readme)** - Core agent features
- **[strands-agents](https://github.com/pydantic/strands-agents)** - Underlying framework
- **[repl-toolkit](https://github.com/your-org/repl-toolkit)** - REPL framework
- **[dataclass-args](https://pypi.org/project/dataclass-args/)** - CLI parsing
- **[profile-config](https://pypi.org/project/profile-config/)** - Configuration management

---

## Feedback

Found an issue with the documentation? Have a suggestion?

1. Check if it's a YACBA or strands-agent-factory question
2. Search existing issues
3. Create a new issue with:
   - What's unclear or missing
   - Suggested improvement
   - Examples if applicable

**YACBA Issues**: [GitHub Issues](https://github.com/your-username/yacba/issues)  
**strands-agent-factory Issues**: [GitHub Issues](https://github.com/JBarmentlo/strands-agent-factory/issues)

---

## License

This documentation is part of the YACBA project and is licensed under the MIT License.
