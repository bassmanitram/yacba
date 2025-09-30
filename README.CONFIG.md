# YACBA Configuration System

YACBA supports a configuration system that allows you to define reusable profiles and settings, reducing the need for long command-line arguments. The system maintains full backward compatibility with raw CLI usage while adding configuration file support.

## Overview

The configuration system uses YAML files with a profile-based approach. You can define multiple profiles for different use cases (development, production, coding, etc.) and easily switch between them or override specific settings.

## Configuration File Discovery

YACBA searches for configuration files in the following order:

1. **Explicit path**: `--config /path/to/config.yaml`
2. **Project-specific**: `./.yacba/config.yaml` or `./.yacba/config.yml`
3. **Alternative project**: `./yacba.config.yaml` or `./yacba.config.yml`
4. **Global user**: `~/.yacba/config.yaml` or `~/.yacba/config.yml`

## Configuration File Structure

```yaml
# Default profile to use when none specified
default_profile: "development"

# Global defaults applied to all profiles
defaults:
  conversation_manager: "sliding_window"
  window_size: 40
  max_files: 10

# Named profiles
profiles:
  development:
    model: "litellm:gemini/gemini-2.5-flash"
    system_prompt: "You are a helpful development assistant with access to tools."
    tool_configs:
      - "~/.yacba/tools/"
      - "./tools/"
    show_tool_use: true
    
  production:
    model: "openai:gpt-4"
    system_prompt: "file://~/.yacba/prompts/production.txt"
    tool_configs:
      - "~/.yacba/tools/production/"
    show_tool_use: false
    conversation_manager: "summarizing"
    session: "prod-session"
    
  coding:
    # Inherit settings from another profile
    inherits: "development"
    model: "anthropic:claude-3-sonnet"
    system_prompt: "You are an expert programmer with access to development tools."
    tool_configs:
      - "~/.yacba/tools/dev/"
      - "./project-tools/"
    files:
      - "README.md"
      - "src/**/*.py"
    max_files: 50
```

## Configuration Options

All CLI options can be specified in configuration files. Here are the most commonly used:

### Core Settings
- `model`: Model string (e.g., `"litellm:gemini/gemini-1.5-flash"`)
- `system_prompt`: System prompt text or `"file://path/to/file"`
- `session`: Session name for persistence
- `headless`: Boolean for headless mode

### Tool Configuration
- `tool_configs`: List of tool configuration directories
- `show_tool_use`: Boolean to show detailed tool usage

### File Handling
- `files`: List of files to upload at startup
- `max_files`: Maximum number of files to process

### Conversation Management
- `conversation_manager`: `"null"`, `"sliding_window"`, or `"summarizing"`
- `window_size`: Messages to keep in sliding window
- `preserve_recent`: Recent messages to preserve in summarizing mode
- `summary_ratio`: Ratio of messages to summarize (0.1-0.8)
- `summarization_model`: Optional separate model for summaries

### Model Configuration
- `model_config`: Path to JSON model config file
- `config_overrides`: List of configuration overrides

## Profile Inheritance

Profiles can inherit from other profiles using the `inherits` key:

```yaml
profiles:
  base:
    model: "litellm:gemini/gemini-1.5-flash"
    conversation_manager: "sliding_window"
    tool_configs: ["~/.yacba/tools/"]
    
  development:
    inherits: "base"
    show_tool_use: true
    system_prompt: "You are a development assistant."
    
  production:
    inherits: "base"
    model: "openai:gpt-4"
    show_tool_use: false
    session: "production"
```

Child profiles override parent settings. Inheritance chains are resolved recursively.

## Template Variables

Configuration values support template variable substitution:

```yaml
profiles:
  project:
    system_prompt: "You are working on the ${PROJECT_NAME} project"
    tool_configs:
      - "${HOME}/.yacba/tools/"
      - "./${PROJECT_NAME}-tools/"
    session: "${PROJECT_NAME}-session"
```

Available variables:
- `${HOME}` or `${USER_HOME}`: User home directory
- `${PROJECT_NAME}`: Current directory name
- Any environment variable: `${CUSTOM_VAR}`

## Configuration Resolution Priority

Settings are resolved in this order (highest to lowest priority):

1. **Command-line arguments** (highest priority)
2. **Profile settings**
3. **Global defaults section**
4. **Built-in defaults** (lowest priority)

## CLI Integration

### New Configuration Commands

```bash
# Create a sample configuration file
yacba --init-config ~/.yacba/config.yaml

# List available profiles
yacba --list-profiles

# Show resolved configuration (for debugging)
yacba --show-config

# Use specific configuration file
yacba --config /path/to/config.yaml

# Use specific profile
yacba --profile production
```

### Usage Examples

```bash
# Use default profile from config file
yacba

# Use specific profile
yacba --profile coding

# Use profile with overrides
yacba --profile development --model "openai:gpt-4" --show-tool-use

# Override individual settings (no profile)
yacba --model "litellm:gemini/gemini-1.5-pro" -t ./tools/

# Headless with profile
yacba --profile production --headless -i "Deploy the application"

# All existing CLI usage continues to work unchanged
yacba -m "openai:gpt-4" -t ./tools/ -s "Custom prompt" --headless -i "Hello"
```

## Setup Workflow

### 1. Create Initial Configuration

```bash
# Create global configuration
yacba --init-config ~/.yacba/config.yaml

# Or create project-specific configuration  
yacba --init-config ./.yacba/config.yaml
```

### 2. Edit Configuration

Edit the created file to add your preferred models, tools, and settings:

```yaml
default_profile: "my-default"

defaults:
  conversation_manager: "sliding_window"
  window_size: 60
  
profiles:
  my-default:
    model: "litellm:gemini/gemini-1.5-flash"
    tool_configs: 
      - "~/my-tools/"
    system_prompt: "You are my personal assistant."
    
  coding:
    inherits: "my-default"
    model: "anthropic:claude-3-sonnet"
    tool_configs:
      - "~/my-tools/"
      - "./project-tools/"
    files: ["README.md", "src/"]
    system_prompt: "You are an expert programmer."
```

### 3. Daily Usage

```bash
# Simple usage with your configured defaults
yacba

# Switch contexts easily
yacba --profile coding

# Override when needed
yacba --profile coding --model "openai:gpt-4"
```

## Project-Specific Configuration

For project-specific setups, create `./.yacba/config.yaml` in your project directory:

```yaml
default_profile: "project"

profiles:
  project:
    model: "litellm:gemini/gemini-1.5-flash"
    system_prompt: "You are working on the ${PROJECT_NAME} project. Help with code analysis and documentation."
    tool_configs:
      - "./tools/"
      - "~/.yacba/tools/dev/"
    files:
      - "README.md"
      - "docs/*.md"
      - "src/**/*.py"
    session: "${PROJECT_NAME}"
    
  testing:
    inherits: "project"
    system_prompt: "Focus on testing and quality assurance for ${PROJECT_NAME}."
    tool_configs:
      - "./test-tools/"
      - "~/.yacba/tools/testing/"
```

## Backward Compatibility

The configuration system is fully backward compatible:

- All existing CLI commands work unchanged
- No configuration file required
- New features are purely additive
- Existing scripts and workflows continue to function

## Advanced Features

### Complex Tool Configurations

```yaml
profiles:
  full-stack:
    tool_configs:
      - "~/.yacba/tools/database/"
      - "~/.yacba/tools/web/"
      - "./project-tools/"
    files:
      - "frontend/**/*.{js,ts,jsx,tsx}"
      - "backend/**/*.py"
      - "database/schema.sql"
    model_config: "./configs/full-stack-model.json"
```

### Environment-Specific Profiles

```yaml
profiles:
  development:
    model: "litellm:gemini/gemini-1.5-flash"  # Fast, cheap
    show_tool_use: true
    conversation_manager: "sliding_window"
    
  production:
    model: "openai:gpt-4"  # High quality
    show_tool_use: false
    conversation_manager: "summarizing"
    summarization_model: "litellm:gemini/gemini-1.5-flash"  # Cheap summaries
```

### Multiple Configuration Files

You can have both global and project-specific configurations:

- `~/.yacba/config.yaml`: Global defaults and personal profiles
- `./.yacba/config.yaml`: Project-specific overrides and profiles

Project configurations automatically override global ones for matching settings.

## Troubleshooting

### Debug Configuration Resolution

```bash
# See what configuration is being used
yacba --show-config

# See available profiles
yacba --list-profiles

# Use explicit config file
yacba --config /path/to/config.yaml --show-config
```

### Common Issues

1. **Profile not found**: Check profile name spelling and file location
2. **Template variables not substituting**: Ensure proper `${VAR}` syntax
3. **Settings not applying**: Check configuration resolution priority
4. **YAML syntax errors**: Validate YAML syntax with online tools

### Validation

YACBA validates configuration files on load and provides helpful error messages for:
- Invalid YAML syntax
- Unknown configuration keys
- Invalid value types
- Missing inherited profiles
- Circular inheritance chains

The configuration system makes YACBA more convenient to use while maintaining all existing functionality. Set up your preferences once, then experience simplified daily usage with consistent, reproducible configurations.
