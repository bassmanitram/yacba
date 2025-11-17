# YACBA Configuration System

YACBA supports a profile-based configuration system that allows you to define reusable settings, reducing the need for long command-line arguments. The system maintains full backward compatibility with raw CLI usage.

## Overview

The configuration system uses two mechanisms:

1. **Profile-based configuration** - YAML files with named profiles, powered by [profile-config](https://pypi.org/project/profile-config/)
2. **Simple configuration files** - Flat JSON/YAML files via `--config`, powered by [dataclass-args](https://pypi.org/project/dataclass-args/)

Both systems can be used together, with clear precedence rules.

## Profile-Based Configuration (Recommended)

### File Locations

YACBA uses profile-config which automatically discovers and merges configuration files:

**Discovered locations** (both are searched and merged):
1. `~/.yacba/config.yaml` (or `.yml`) - User-wide configuration
2. `./.yacba/config.yaml` (or `.yml`) - Project-specific configuration

**Precedence**: Project config overrides user config for the same keys. Missing keys in project config are filled from user config.

This allows you to:
- Set user-wide defaults in your home directory
- Override specific settings per-project
- Share project configs in version control

### Profile Configuration Structure

```yaml
# Global defaults applied to all profiles
defaults:
  conversation_manager_type: sliding_window
  sliding_window_size: 40
  max_files: 10

# Named profiles
profiles:
  development:
    model_string: "litellm:gemini/gemini-2.5-flash"
    system_prompt: "You are a helpful development assistant with access to tools."
    tool_configs_dir: "~/.yacba/tools/"
    show_tool_use: true
    
  production:
    model_string: "openai:gpt-4"
    system_prompt: "@~/.yacba/prompts/production.txt"  # Load from file
    tool_configs_dir: "~/.yacba/tools/production/"
    show_tool_use: false
    conversation_manager_type: summarizing
    session_name: "prod-session"
    
  coding:
    # Inherit settings from another profile
    inherits: development
    model_string: "anthropic:claude-3-sonnet"
    system_prompt: "You are an expert programmer with access to development tools."
    tool_configs_dir: "~/.yacba/tools/dev/"
    max_files: 50
```

### Profile Selection

Profiles are selected via:

1. **CLI argument**: `yacba --profile name` (highest priority)
2. **Environment variable**: `export YACBA_PROFILE=name`
3. **Default fallback**: `'default'` profile is used if not specified

**Example:**
```bash
# Uses 'default' profile from config
yacba

# Uses 'production' profile
yacba --profile production

# Uses profile from environment
export YACBA_PROFILE=development
yacba
```

### Profile Features

- **Multiple profiles**: Switch between different configurations easily
- **Inheritance**: Profiles can inherit from other profiles with `inherits: base_profile`
- **Defaults section**: Common settings applied to all profiles
- **File loading**: Use `@filename.txt` to load content from files
- **Hierarchical merging**: User-wide + project-specific configs merged automatically

## Simple Configuration Files

In addition to profile-based configuration, you can use simple JSON or YAML files with `--config`:

**Example (`my-config.json`):**
```json
{
  "model_string": "gpt-4o",
  "system_prompt": "You are a helpful assistant",
  "show_tool_use": true,
  "conversation_manager_type": "summarizing"
}
```

**Usage:**
```bash
yacba --config my-config.json
```

**Important differences from profile-config:**
- `--config` files do NOT support profiles, inheritance, or defaults sections
- They are simple flat key-value pairs
- They override profile-config but are overridden by CLI arguments
- Use profile-config (`.yacba/config.yaml`) for structured configurations with multiple profiles

## Configuration Options

All CLI options can be specified in configuration files. Field names match the YacbaConfig dataclass:

### Core Settings
- `model_string`: Model identifier (e.g., `"litellm:gemini/gemini-1.5-flash"`)
- `system_prompt`: System prompt text or `"@path/to/file"` to load from file
- `session_name`: Session name for persistence
- `headless`: Boolean for headless mode (default: false)
- `initial_message`: Initial message or `"@path/to/file"`

### Tool Configuration
- `tool_configs_dir`: Directory containing tool configuration files
- `show_tool_use`: Boolean to show detailed tool usage (default: false)

### File Handling
- `max_files`: Maximum number of files to process (default: 20)

### Conversation Management
- `conversation_manager_type`: `null`, `sliding_window`, or `summarizing` (default: `sliding_window`)
- `sliding_window_size`: Messages to keep in sliding window (default: 40)
- `preserve_recent_messages`: Recent messages to preserve in summarizing mode (default: 10)
- `summary_ratio`: Ratio for summarization 0.0-1.0 (default: 0.3)
- `summarization_model`: Optional separate model for summaries
- `custom_summarization_prompt`: Custom prompt for summarization or `"@path/to/file"`
- `should_truncate_results`: Truncate long tool results (default: true)

### Model Configuration
- `model_config`: Dictionary of model configuration parameters
- `summarization_model_config`: Dictionary for summarization model config
- `emulate_system_prompt`: Use user message for system prompt (default: false)
- `disable_context_repair`: Disable automatic context repair (default: false)

### Session & Agent
- `agent_id`: Agent identifier for session management

### Output & UI
- `cli_prompt`: Custom CLI prompt string or `"@path/to/file"`
- `response_prefix`: Custom response prefix or `"@path/to/file"`

## File Loading Syntax

Use `@` prefix to load content from files:

```yaml
profiles:
  production:
    system_prompt: "@~/.yacba/prompts/production.txt"
    initial_message: "@./messages/startup.txt"
    custom_summarization_prompt: "@~/prompts/summary.txt"
```

**Supported fields**:
- `system_prompt`
- `initial_message`
- `custom_summarization_prompt`
- `cli_prompt`
- `response_prefix`

## Profile Inheritance

Profiles can inherit from other profiles using the `inherits` key:

```yaml
profiles:
  base:
    model_string: "litellm:gemini/gemini-1.5-flash"
    conversation_manager_type: sliding_window
    tool_configs_dir: "~/.yacba/tools/"
    
  development:
    inherits: base
    show_tool_use: true
    system_prompt: "You are a development assistant."
    
  production:
    inherits: base
    model_string: "openai:gpt-4"
    show_tool_use: false
    session_name: production
```

Child profiles override parent settings. Inheritance is resolved by profile-config.

## Variable Interpolation

Profile-config supports variable interpolation (enabled by default in YACBA).

Consult the [profile-config documentation](https://pypi.org/project/profile-config/) for interpolation syntax details.

## Configuration Resolution Priority

Settings are resolved in this order (highest to lowest priority):

1. **Command-line arguments** - Direct CLI flags (highest priority)
2. **Simple config file** - File specified with `--config`
3. **Environment variables** - `YACBA_*` prefixed variables (scalars only)
4. **Project profile config** - `./.yacba/config.yaml` 
5. **User profile config** - `~/.yacba/config.yaml`
6. **Built-in defaults** - Hard-coded fallbacks (lowest priority)

**Example:**
```bash
# User config: model_string: "gemini-2.5-flash"
# Project config: model_string: "gpt-4o", show_tool_use: true
# Environment: YACBA_SESSION_NAME="my-session"
# CLI: --system-prompt "You are a code reviewer"

# Result:
#   model_string: "gpt-4o"  (project config overrides user config)
#   show_tool_use: true  (from project config)
#   session_name: "my-session"  (from environment)
#   system_prompt: "You are a code reviewer"  (from CLI, highest priority)
```

**Implementation:**
- profile-config merges: defaults → user config → project config → env vars
- dataclass-args adds: profile result → `--config` file → CLI args

## Environment Variables

Scalar configuration fields can be set via `YACBA_*` environment variables:

**Core Configuration:**
```bash
YACBA_MODEL_STRING="gpt-4o"
YACBA_SYSTEM_PROMPT="You are a helpful assistant"
YACBA_EMULATE_SYSTEM_PROMPT="false"
YACBA_DISABLE_CONTEXT_REPAIR="false"
```

**Session and Files:**
```bash
YACBA_SESSION_NAME="my-session"
YACBA_AGENT_ID="my-agent"
YACBA_TOOL_CONFIGS_DIR="./tools"
YACBA_MAX_FILES="20"
```

**Conversation Management:**
```bash
YACBA_CONVERSATION_MANAGER_TYPE="sliding_window"
YACBA_SLIDING_WINDOW_SIZE="40"
YACBA_PRESERVE_RECENT_MESSAGES="10"
YACBA_SUMMARY_RATIO="0.3"
YACBA_SUMMARIZATION_MODEL="gpt-4o-mini"
YACBA_CUSTOM_SUMMARIZATION_PROMPT="Provide a summary..."
YACBA_SHOULD_TRUNCATE_RESULTS="true"
```

**Execution and Display:**
```bash
YACBA_HEADLESS="false"
YACBA_INITIAL_MESSAGE="Hello"
YACBA_SHOW_TOOL_USE="true"
YACBA_CLI_PROMPT="> "
YACBA_RESPONSE_PREFIX="Assistant: "
```

**Note**: Complex configurations like `model_config` and `summarization_model_config` cannot be set via environment variables. Use configuration files or CLI arguments with `--model-config` and `--mc` instead.

Environment variables override profile settings but are overridden by `--config` files and CLI arguments.

## Meta-Arguments

Configuration-related commands:

```bash
# Create a sample configuration file
yacba --init-config ~/.yacba/config.yaml

# List available profiles from config file
yacba --list-profiles

# Show resolved configuration (debugging)
yacba --show-config

# Use specific profile
yacba --profile production

# Profile via environment variable
export YACBA_PROFILE=development
yacba
```

## Usage Examples

```bash
# Use default profile from ~/.yacba/config.yaml
yacba

# Use specific profile
yacba --profile coding

# Use profile with overrides
yacba --profile development --model-string "openai:gpt-4" --show-tool-use

# Use simple config file
yacba --config my-settings.json

# Override without profile (uses defaults + env vars)
yacba --model-string "litellm:gemini/gemini-1.5-pro"

# Headless with profile
yacba --profile production --headless -i "Deploy the application"

# All existing CLI usage continues to work unchanged
yacba -m "openai:gpt-4" -s "Custom prompt" --headless -i "Hello"
```

## Setup Workflow

### 1. Create Configuration File

```bash
# Create global configuration at recommended location
yacba --init-config ~/.yacba/config.yaml
```

This creates a sample configuration with common profiles.

### 2. Edit Configuration

Edit `~/.yacba/config.yaml` to add your preferred settings:

```yaml
defaults:
  conversation_manager_type: sliding_window
  sliding_window_size: 60
  
profiles:
  default:
    model_string: "litellm:gemini/gemini-1.5-flash"
    tool_configs_dir: "~/my-tools/"
    system_prompt: "You are my personal assistant."
    
  coding:
    inherits: default
    model_string: "anthropic:claude-3-sonnet"
    system_prompt: "You are an expert programmer."
```

### 3. Optional: Create Project-Specific Config

For project-specific settings:

```bash
mkdir -p ./.yacba
cat > ./.yacba/config.yaml << 'EOF'
profiles:
  default:
    tool_configs_dir: "./tools"
    session_name: "my-project"
    model_string: "gpt-4o"
EOF
```

Settings in `./.yacba/config.yaml` override `~/.yacba/config.yaml`.

### 4. Daily Usage

```bash
# Simple usage with configured defaults
yacba

# Switch profiles easily
yacba --profile coding

# Override when needed
yacba --profile coding --model-string "openai:gpt-4"
```

## Sample Configuration

Complete example with multiple profiles:

```yaml
defaults:
  conversation_manager_type: sliding_window
  sliding_window_size: 40
  max_files: 10
  should_truncate_results: true

profiles:
  default:
    model_string: "litellm:gemini/gemini-1.5-flash"
    system_prompt: "You are a helpful assistant."
    tool_configs_dir: "~/.yacba/tools/"
    show_tool_use: false

  development:
    inherits: default
    system_prompt: "You are a helpful development assistant with access to tools."
    show_tool_use: true
    model_config:
      temperature: 0.7
      max_tokens: 2000
    
  production:
    model_string: "openai:gpt-4"
    system_prompt: "@~/.yacba/prompts/production.txt"
    tool_configs_dir: "~/.yacba/tools/production/"
    show_tool_use: false
    conversation_manager_type: summarizing
    session_name: "prod-session"
    model_config:
      temperature: 0.3
      max_tokens: 4000
    
  coding:
    inherits: development
    model_string: "anthropic:claude-3-sonnet"
    system_prompt: "You are an expert programmer with access to development tools."
    tool_configs_dir: "~/.yacba/tools/dev/"
    max_files: 50
    
  testing:
    inherits: development
    system_prompt: "Focus on testing and quality assurance."
    tool_configs_dir: "~/.yacba/tools/testing/"
    conversation_manager_type: null  # No conversation management
```

## Backward Compatibility

The configuration system is fully backward compatible:

- All existing CLI commands work unchanged
- No configuration file required
- New features are purely additive
- Existing scripts and workflows continue to function

## Troubleshooting

### Debug Configuration Resolution

```bash
# See resolved configuration
yacba --show-config

# See available profiles
yacba --list-profiles

# Check profile with overrides
yacba --profile development --show-config
```

### Common Issues

1. **Profile not found**: Check spelling and that profile exists in config file
2. **Configuration file not found**: Ensure it's at `~/.yacba/config.yaml` or `./.yacba/config.yaml`
3. **Settings not applying**: Check precedence (CLI args override everything)
4. **File loading fails**: Check `@` syntax and file paths
5. **YAML syntax errors**: Validate YAML with online tools or `yamllint`

### Validation

YACBA validates configuration and provides error messages for:
- Invalid YAML syntax
- Unknown configuration keys (warnings)
- Invalid value types
- Missing inherited profiles
- Circular inheritance chains (detected by profile-config)

## Field Name Reference

Common field name mappings (use exact names in config files):

| CLI Argument | Config Field Name |
|--------------|------------------|
| `-m, --model-string` | `model_string` |
| `-s, --system-prompt` | `system_prompt` |
| `-H, --headless` | `headless` |
| `-i, --initial-message` | `initial_message` |
| `--session-name` | `session_name` |
| `--model-config` | `model_config` |
| `--conversation-manager-type` | `conversation_manager_type` |
| `--sliding-window-size` | `sliding_window_size` |
| `--preserve-recent-messages` | `preserve_recent_messages` |
| `--summary-ratio` | `summary_ratio` |
| `--summarization-model` | `summarization_model` |
| `--show-tool-use` | `show_tool_use` |
| `--max-files` | `max_files` |

Use `yacba --help` to see all available options.

## Notes

- Configuration powered by [profile-config](https://pypi.org/project/profile-config/)
- CLI parsing powered by [dataclass-args](https://pypi.org/project/dataclass-args/)
- Both `~/.yacba/config.yaml` and `./.yacba/config.yaml` are discovered and merged
- Project config overrides user config for the same keys
- Profile inheritance and interpolation handled by profile-config
- Field names must match YacbaConfig dataclass exactly
- Use `@` prefix for file loading, not `file://`
- Environment variables support scalar values only (not dicts)

The configuration system makes YACBA more convenient while maintaining all existing functionality. Set up your preferences once, then enjoy simplified daily usage with consistent, reproducible configurations.
