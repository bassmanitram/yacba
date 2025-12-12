# Migration Guide: Nested Configuration Structure

**Breaking Change**: YACBA configuration has been restructured to use nested sections.

## Overview

YACBA's configuration has been refactored to use a nested structure with `cli_nested` from dataclass-args. This eliminates the configuration converter and provides type-safe, direct access to `AgentFactoryConfig`.

### What Changed

**Before** (Flat structure):
```yaml
# Old flat config
model_string: "litellm:gemini/gemini-1.5-flash"
session_name: "my-session"
system_prompt: "You are a helpful assistant"
tool_configs_dir: "~/.yacba/tools"
headless: false
max_files: 20
```

**After** (Nested structure):
```yaml
# New nested config
agent:
  model: "litellm:gemini/gemini-1.5-flash"
  session_id: "my-session"
  system_prompt: "You are a helpful assistant"
  tool_config_paths:
    - "~/.yacba/tools/*.json"
repl:
  headless: false
  max_files: 20
```

## Required Changes

### 1. Configuration Files

**Profile configs** (`.yacba/config.yaml` or `~/.yacba/config.yaml`):

```yaml
# Old format
profiles:
  development:
    model_string: "litellm:gemini/gemini-1.5-flash"
    session_name: "dev-session"
    tool_configs_dir: "~/.yacba/tools"
    max_files: 30

# New format
profiles:
  development:
    agent:
      model: "litellm:gemini/gemini-1.5-flash"
      session_id: "dev-session"
      tool_config_paths:
        - "~/.yacba/tools/*.json"
    repl:
      max_files: 30
```

**Standalone config files** (used with `--config`):

```yaml
# Old format
model_string: "openai:gpt-4"
system_prompt: "Custom prompt"
headless: true

# New format
agent:
  model: "openai:gpt-4"
  system_prompt: "Custom prompt"
repl:
  headless: true
```

### 2. Environment Variables

Environment variables must now use nested structure prefixes:

```bash
# Old format
export YACBA_MODEL_STRING="litellm:gemini/gemini-1.5-flash"
export YACBA_SESSION_NAME="my-session"
export YACBA_HEADLESS="true"

# New format
export YACBA_AGENT_MODEL="litellm:gemini/gemini-1.5-flash"
export YACBA_AGENT_SESSION_ID="my-session"
export YACBA_REPL_HEADLESS="true"
```

### 3. Field Name Changes

Several fields were renamed for consistency:

| Old Name (Flat) | New Name (Nested) | Section |
|-----------------|-------------------|---------|
| `model_string` | `model` | `agent` |
| `session_name` | `session_id` | `agent` |
| `tool_configs_dir` | `tool_config_paths` | `agent` |

**Note**: `tool_config_paths` is now a **list of glob patterns**, not a single directory.

### 4. Code Changes

If you programmatically create configurations:

```python
# Old code
from config import YacbaConfig
config = YacbaConfig(
    model_string="gpt-4",
    session_name="my-session",
    headless=True
)

# New code
from config import YacbaConfig
from strands_agent_factory import AgentFactoryConfig

config = YacbaConfig(
    agent=AgentFactoryConfig(
        model="gpt-4",
        session_id="my-session"
    ),
    repl=YacbaREPLConfig(
        headless=True
    )
)
```

Accessing fields:

```python
# Old code
model = config.model_string
session = config.session_name
headless = config.headless

# New code
model = config.agent.model
session = config.agent.session_id
headless = config.repl.headless
```

## CLI Arguments (No Changes)

The CLI interface remains **unchanged**. All flags work exactly as before:

```bash
# These commands work the same
yacba -m "gpt-4" -s "Custom prompt" -H
yacba --model "claude-3" --session-id "my-session"
yacba -t "~/.yacba/tools/*.json" -f input.txt
```

## Benefits of New Structure

1. **Type Safety**: `config.agent` IS `AgentFactoryConfig` - no converter needed
2. **Clear Separation**: Agent config vs REPL config are distinct
3. **Reduced Duplication**: No need to maintain field mappings
4. **Better Organization**: Config files are more readable with sections
5. **Glob Patterns**: `tool_config_paths` now supports multiple glob patterns

## Migration Script

To help migrate your configuration files:

```bash
# Generate new sample config to see structure
yacba --init-config ~/.yacba/config.yaml

# Show current resolved config
yacba --show-config
```

## Tool Config Paths Migration

The `tool_configs_dir` field has been replaced with `tool_config_paths` (a list):

```yaml
# Old
tool_configs_dir: "~/.yacba/tools"

# New - automatically converts directory to glob pattern
tool_config_paths:
  - "~/.yacba/tools/*.json"

# Or use multiple paths
tool_config_paths:
  - "~/.yacba/tools/core/*.json"
  - "~/.yacba/tools/optional/*.json"
  - "/path/to/project/tools/*.json"
```

## Common Issues

### 1. "Unknown field" error

**Error**: `Unknown field 'model_string' in configuration`

**Solution**: Change to nested structure:
```yaml
# Wrong
model_string: "gpt-4"

# Correct
agent:
  model: "gpt-4"
```

### 2. Environment variables not working

**Error**: Environment variables like `YACBA_MODEL_STRING` ignored

**Solution**: Use nested prefixes:
```bash
# Wrong
export YACBA_MODEL_STRING="gpt-4"

# Correct
export YACBA_AGENT_MODEL="gpt-4"
```

### 3. Profile config not loading

**Problem**: Old flat profile config doesn't load

**Solution**: Restructure profile config with nested sections:
```yaml
profiles:
  my-profile:
    agent:
      model: "..."
    repl:
      headless: false
```

## Getting Help

If you encounter issues during migration:

1. Check current config: `yacba --show-config`
2. Generate sample config: `yacba --init-config sample-config.yaml`
3. Check logs: Look for "Unknown field" or "ConfigurationError" messages
4. File an issue with your config file (redact sensitive values)

## Timeline

- **Version X.Y.Z**: Nested config introduced, backward compatibility removed
- **Future**: Nested structure is now the only supported format

## Questions?

For questions or issues:
- File an issue on GitHub
- Check documentation at `docs/`
- Run `yacba --help` for current CLI options
