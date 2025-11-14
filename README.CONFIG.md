# YACBA Configuration System

YACBA supports a profile-based configuration system that allows you to define reusable settings, reducing the need for long command-line arguments. The system maintains full backward compatibility with raw CLI usage.

## Overview

The configuration system uses YAML files with profiles powered by the [profile-config](https://pypi.org/project/profile-config/) library. You can define multiple profiles for different use cases and easily switch between them or override specific settings.

## Configuration File Locations

YACBA searches for configuration files in:

1. **Home directory**: `~/.yacba/config.yaml` (or `config.yml`)
2. **Explicit path**: Via `--config` flag in dataclass-args (not profile-config search)

**Note**: profile-config with `search_home=True` only searches the home directory. Project-specific config files would need to be explicitly specified via `--config`.

## Configuration File Structure

```yaml
# Default profile to use when none specified
default_profile: development

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

## Configuration Options

All CLI options can be specified in configuration files. Field names match the YacbaConfig dataclass:

### Core Settings
- `model_string`: Model identifier (e.g., `"litellm:gemini/gemini-1.5-flash"`)
- `system_prompt`: System prompt text or `"@path/to/file"` to load from file
- `session_name`: Session name for persistence
- `headless`: Boolean for headless mode (default: false)
- `initial_message`: Initial message or `"@path/to/file"`

### Tool Configuration
- `tool_configs_dir`: Directory containing .tools.json files (converted to paths internally)
- `show_tool_use`: Boolean to show detailed tool usage (default: false)

### File Handling
- `max_files`: Maximum number of files to process (default: 20)

### Conversation Management
- `conversation_manager_type`: `null`, `sliding_window`, or `summarizing` (default: `sliding_window`)
- `sliding_window_size`: Messages to keep in sliding window (default: 40)
- `preserve_recent_messages`: Recent messages to preserve in summarizing mode (default: 10)
- `summary_ratio`: Ratio for summarization 0.0-1.0 (default: 0.3)
- `summarization_model`: Optional separate model for summaries
- `summarization_model_config`: Config for summarization model
- `custom_summarization_prompt`: Custom prompt for summarization or `"@path/to/file"`
- `should_truncate_results`: Truncate long tool results (default: true)

### Model Configuration
- `model_config`: Dictionary of model configuration parameters
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

Profile-config supports variable interpolation (controlled by `enable_interpolation` parameter, enabled by default in YACBA).

The exact syntax depends on the profile-config library's interpolation implementation. Consult the [profile-config documentation](https://pypi.org/project/profile-config/) for details.

## Configuration Resolution Priority

Settings are resolved in this order (highest to lowest priority):

1. **Command-line arguments** (highest priority)
2. **--config file** (if specified via dataclass-args)
3. **Environment variables** (YACBA_* prefix)
4. **Profile settings** (from profile-config)
5. **Global defaults section** (in config file)
6. **Built-in defaults** (lowest priority)

Implementation: profile-config resolves DEFAULTS → PROFILE → ENV, then dataclass-args adds --config → CLI args.

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
default_profile: my-default

defaults:
  conversation_manager_type: sliding_window
  sliding_window_size: 60
  
profiles:
  my-default:
    model_string: "litellm:gemini/gemini-1.5-flash"
    tool_configs_dir: "~/my-tools/"
    system_prompt: "You are my personal assistant."
    
  coding:
    inherits: my-default
    model_string: "anthropic:claude-3-sonnet"
    system_prompt: "You are an expert programmer."
```

### 3. Daily Usage

```bash
# Simple usage with configured defaults
yacba

# Switch profiles easily
yacba --profile coding

# Override when needed
yacba --profile coding --model-string "openai:gpt-4"
```

## Environment Variables

All configuration fields can be set via `YACBA_*` environment variables:

```bash
export YACBA_MODEL_STRING="openai:gpt-4"
export YACBA_SYSTEM_PROMPT="You are an expert programmer"
export YACBA_SESSION_NAME="my-session"
export YACBA_SHOW_TOOL_USE="true"
export YACBA_PROFILE="production"
```

Environment variables override profile settings but are overridden by CLI arguments.

## Sample Configuration

Complete example with multiple profiles:

```yaml
default_profile: development

defaults:
  conversation_manager_type: sliding_window
  sliding_window_size: 40
  max_files: 10
  should_truncate_results: true

profiles:
  development:
    model_string: "litellm:gemini/gemini-1.5-flash"
    system_prompt: "You are a helpful development assistant with access to tools."
    tool_configs_dir: "~/.yacba/tools/"
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
2. **Configuration file not found**: Ensure it's at `~/.yacba/config.yaml`
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
- File discovery searches `~/.yacba/config.yaml` by default
- Profile inheritance and interpolation handled by profile-config
- Field names must match YacbaConfig dataclass exactly
- Use `@` prefix for file loading, not `file://`

The configuration system makes YACBA more convenient while maintaining all existing functionality. Set up your preferences once, then enjoy simplified daily usage with consistent, reproducible configurations.
