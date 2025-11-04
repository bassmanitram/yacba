# YACBA Documentation

Welcome to the YACBA (Yet Another ChatBot Agent) documentation!

## Documentation Overview

This directory contains comprehensive documentation for YACBA's architecture, API, and troubleshooting.

### Core Documentation

1. **[API Documentation](API.md)** - Complete API reference
   - Configuration system
   - Adapters
   - Utilities
   - Type definitions
   - Usage examples

2. **[Architecture Documentation](ARCHITECTURE.md)** - System design and architecture
   - High-level architecture
   - Component diagrams
   - Data flow
   - Design patterns
   - Extension points

3. **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Problem solving and debugging
   - Quick diagnostics
   - Common issues
   - Configuration problems
   - Tool loading issues
   - Debugging techniques

### Additional Resources

- **[Main README](../README.md)** - Quick start and feature overview
- **[Configuration Guide](../README.CONFIG.md)** - Configuration system details
- **[Model Configuration Guide](../README.MODEL_CONFIG.md)** - Model config parsing

---

## Quick Links

### Getting Started
- **[Completion System](COMPLETION_SYSTEM.md)** - Tab completion system details

- [Installation](../README.md#installation)
- [Basic Examples](../README.md#basic-examples)
- [Quick Start](../README.md#quick-start)

### Configuration

- [CLI Arguments](API.md#configuration-system)
- [Configuration Precedence](ARCHITECTURE.md#configuration-precedence)
- [Profile System](ARCHITECTURE.md#profile-system)
- [Environment Variables](API.md#constants)

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
├── API.md                 # Complete API reference
├── ARCHITECTURE.md        # Architecture and design documentation
└── TROUBLESHOOTING.md     # Troubleshooting and debugging guide
```

---

## Key Concepts

### Architecture

YACBA is built on a **modular, adapter-based architecture** with three main components:

1. **YACBA Core** - Configuration, CLI, orchestration
2. **strands-agent-factory** - Agent lifecycle, tools, AI integration
3. **repl-toolkit** - Interactive/headless UI

See [Architecture Documentation](ARCHITECTURE.md) for details.

### Configuration System

YACBA uses a **5-level configuration precedence system**:

1. Default values (lowest)
2. Environment variables
3. Discovered config files
4. User-specified config file
5. CLI arguments (highest)

See [Configuration System](ARCHITECTURE.md#configuration-system) for details.

### Adapter Pattern

YACBA uses **adapters** to bridge between packages:

- **YacbaToStrandsConfigConverter** - Config conversion
- **YacbaBackend** - Backend protocol implementation
- **YacbaCompleter** - Tab completion (with alphabetically sorted commands)
- **YacbaActionRegistry** - Command system

See [Adapter Pattern](ARCHITECTURE.md#adapter-pattern-implementation) for details.

---

## Available Commands

YACBA provides these built-in commands (alphabetically sorted in tab completion):

- `/clear` - Clear conversation history
- `/conversation-manager` - Change conversation management strategy
- `/conversation-stats` - Show conversation statistics
- `/exit` - Exit the application
- `/help` - Show available commands
- `/history` - Show conversation history
- `/info` - Show session information (alias for `/status`)
- `/quit` - Exit the application
- `/session` - Session management (save, load, list)
- `/shell` - Execute shell commands
- `/shortcuts` - Show keyboard shortcuts
- `/stats` - Show session information (alias for `/status`)
- `/status` - Show comprehensive session status
- `/tools` - List available tools

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
python code/yacba.py --model gpt-4o

# Trace level (very verbose)
export LOGURU_LEVEL=TRACE
python code/yacba.py --model gpt-4o
```

### Test Components

```python
# Test configuration parsing
PYTHONPATH=code python -c "
from config import parse_config
import sys
sys.argv = ['test', '--model', 'gpt-4o', '--show-config']
config = parse_config()
"

# Test adapter conversion
PYTHONPATH=code python -c "
from config import parse_config
from adapters.strands_factory import YacbaToStrandsConfigConverter
import sys
sys.argv = ['test', '--model', 'gpt-4o']
config = parse_config()
converter = YacbaToStrandsConfigConverter(config)
strands_config = converter.convert()
print('Conversion successful')
"
```

---

## API Reference Quick Links

### Configuration

- [ArgumentDefinition](API.md#argumentdefinition)
- [YacbaConfig](API.md#yacbaconfig)
- [parse_config()](API.md#parse_config---yacbaconfig)

### Adapters

- [YacbaToStrandsConfigConverter](API.md#yacbatostrandsconfigconverter)
- [YacbaBackend](API.md#yacbabackend)
- [YacbaActionRegistry](API.md#yacbaactionregistry)

### Utilities

- [discover_tool_configs()](API.md#discover_tool_configs)
- [ModelConfigParser](API.md#modelconfigparser)
- [parse_model_config()](API.md#parse_model_config)

---

## Architecture Quick Links

### Diagrams

- [System Context](ARCHITECTURE.md#system-context)
- [Component Interaction](ARCHITECTURE.md#component-interaction-diagram)
- [Configuration Flow](ARCHITECTURE.md#configuration-flow)
- [Message Flow](ARCHITECTURE.md#message-flow-interactive-mode)

### Design

- [Design Patterns](ARCHITECTURE.md#design-patterns)
- [Module Structure](ARCHITECTURE.md#module-structure)
- [Extension Points](ARCHITECTURE.md#extension-points)

---

## Troubleshooting Quick Links

### Diagnostics

- [Quick Diagnostics](TROUBLESHOOTING.md#quick-diagnostics)
- [Enable Debug Logging](TROUBLESHOOTING.md#enable-debug-logging)
- [Test Components](TROUBLESHOOTING.md#test-components-individually)

### Common Issues

- [Module not found](TROUBLESHOOTING.md#issue-module-not-found-errors)
- [API key not found](TROUBLESHOOTING.md#issue-api-key-not-found-errors)
- [Model not found](TROUBLESHOOTING.md#issue-model-not-found-or-invalid-model-errors)
- [Application hangs](TROUBLESHOOTING.md#issue-application-hangs-or-freezes)

### Specific Problems

- [Configuration Problems](TROUBLESHOOTING.md#configuration-problems)
- [Tool Loading Issues](TROUBLESHOOTING.md#tool-loading-issues)
- [Model Connection Problems](TROUBLESHOOTING.md#model-connection-problems)
- [File Processing Issues](TROUBLESHOOTING.md#file-processing-issues)

---

## Contributing to Documentation

### Documentation Standards

1. **Clear and Concise** - Use simple language
2. **Examples** - Provide code examples
3. **Cross-references** - Link to related sections
4. **Up-to-date** - Keep in sync with code

### Adding Documentation

1. **API Changes** - Update [API.md](API.md)
2. **Architecture Changes** - Update [ARCHITECTURE.md](ARCHITECTURE.md)
3. **New Issues** - Add to [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
4. **Update Index** - Update this README.md

### Documentation Format

- Use Markdown
- Include code examples
- Add diagrams where helpful
- Cross-reference related sections

---

## Version Information

- **YACBA Version**: 2.0 (Refactored Architecture)
- **Documentation Version**: 1.0
- **Last Updated**: 2024-10-30

---

## Feedback

Found an issue with the documentation? Have a suggestion?

1. Check existing documentation
2. Search for similar issues
3. Create a new issue with:
   - What's unclear or missing
   - Suggested improvement
   - Examples if applicable

---

## License

This documentation is part of the YACBA project and is licensed under the MIT License.