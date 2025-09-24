# YACBA Architecture Overview

## Command System Architecture

YACBA uses a sophisticated two-tier command system that maintains clean separation of concerns:

### Tier 1: Framework-Agnostic Commands (`cli/commands/`)
- **Purpose**: Pure CLI infrastructure with no backend dependencies
- **Examples**: `/help`, `/exit`, basic utilities
- **Characteristics**:
  - No knowledge of Strands or specific agent implementations
  - Can work with any backend implementation
  - Provides base command infrastructure and interfaces

### Tier 2: Backend-Specific Commands (`adapters/cli/commands/`)
- **Purpose**: Strands-aware command implementations
- **Examples**: `/tools`, `/session`, `/clear`
- **Characteristics**:
  - Depend on YacbaEngine and Strands infrastructure
  - Extend the base command system with backend-specific functionality
  - Follow the adapter pattern used throughout YACBA

## Benefits of This Architecture

1. **Framework Agnostic**: CLI infrastructure can work with non-Strands backends
2. **Clean Separation**: Clear boundaries between generic and specific functionality
3. **Extensible**: Other agent frameworks can provide their own command adapters
4. **Testable**: Can test CLI infrastructure independently of Strands
5. **Maintainable**: Developers understand which commands depend on what

## Core Components

### Engine Layer
- `YacbaEngine`: Core, UI-agnostic engine managing agent, tools, and model
- `YacbaManager`: Resource manager orchestrating the engine lifecycle
- `YacbaAgent`: Strands-specific agent implementation

### Configuration Layer
- `YacbaConfig`: Central configuration management
- `config_parser.py`: Configuration parsing and validation

### Adapter Layer
- `adapters/framework/`: Model framework adapters (OpenAI, Anthropic, Bedrock, etc.)
- `adapters/tools/`: Tool system adapters (MCP, Python modules, etc.)
- `adapters/cli/`: Strands-aware CLI command adapters

### Interface Layer
- `cli/`: Framework-agnostic CLI infrastructure
- `utils/`: Pure utility functions
- `yacba_types/`: Comprehensive type definitions