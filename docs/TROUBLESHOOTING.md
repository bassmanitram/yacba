# YACBA Troubleshooting Guide

## Overview

This guide provides solutions to **YACBA-specific issues** - problems with the CLI wrapper, configuration management, and REPL interface.

> **Note**: YACBA is built on [strands-agent-factory](https://github.com/JBarmentlo/strands-agent-factory).  
> For **core agent issues** (LLM connections, tool execution, conversation management), see  
> [strands-agent-factory troubleshooting](https://github.com/JBarmentlo/strands-agent-factory#troubleshooting).

### When to Use This Guide vs strands-agent-factory Docs

**Use this guide for**:
- CLI argument parsing issues
- Configuration file problems
- Profile loading errors
- Interactive REPL issues
- Tab completion problems
- File glob/MIME detection issues

**Use strands-agent-factory docs for**:
- LLM API connection errors
- Tool loading/execution failures
- Conversation management issues
- A2A (Agent-to-Agent) setup problems
- Session persistence errors
- Model response issues

---

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Common Issues](#common-issues)
3. [Configuration Problems](#configuration-problems)
4. [Tool Loading Issues](#tool-loading-issues)
5. [Model Connection Problems](#model-connection-problems)
6. [File Processing Issues](#file-processing-issues)
7. [Session Management Problems](#session-management-problems)
8. [Performance Issues](#performance-issues)
9. [Debugging Techniques](#debugging-techniques)
10. [Getting Help](#getting-help)

---

## Quick Diagnostics

### Check Installation

```bash
# Verify Python version (3.10+ required)
python --version

# Check YACBA can be imported
cd /path/to/yacba
PYTHONPATH=code python -c "from config import parse_config; print('YACBA imports OK')"

# Verify dependencies
pip list | grep -E "strands-agent-factory|repl-toolkit|profile-config|dataclass-args"
```

### Verify Configuration

```bash
# Show resolved configuration
python code/yacba.py --show-config

# List available profiles
python code/yacba.py --list-profiles

# Test with minimal config
python code/yacba.py -m "gpt-4o" -H -i "test"
```
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

---

## Common Issues

### Issue: "Module not found" errors

**Symptoms**:
```
ModuleNotFoundError: No module named 'strands_agent_factory'
ModuleNotFoundError: No module named 'repl_toolkit'
```

**Causes**:
- Missing dependencies
- Wrong Python environment
- Incorrect PYTHONPATH

**Solutions**:

1. **Install dependencies**:
```bash
cd /path/to/yacba/code
pip install -r requirements.txt
```

2. **Verify virtual environment**:
```bash
which python  # Should point to .venv/bin/python
pip list | grep strands-agent-factory
```

3. **Set PYTHONPATH**:
```bash
export PYTHONPATH=/path/to/yacba/code:$PYTHONPATH
python yacba.py --help
```

4. **Reinstall in development mode**:
```bash
cd /path/to/yacba/code
pip install -e .
```

---

### Issue: "API key not found" errors

**Symptoms**:
```
Error: OpenAI API key not found
Error: Anthropic API key not configured
```

**Causes**:
- Missing API key environment variables
- Wrong environment variable names
- API keys not exported

**Solutions**:

1. **Set API keys**:
```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Google (for Gemini via LiteLLM)
export GOOGLE_API_KEY="..."

# AWS Bedrock
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"
```

2. **Verify keys are set**:
```bash
echo $OPENAI_API_KEY | head -c 10  # Should show "sk-..."
```

3. **Add to shell profile** (persistent):
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.bashrc
source ~/.bashrc
```

4. **Use .env file** (if supported):
```bash
# Create .env file
cat > .env << EOF
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
EOF

# Load before running
source .env
python code/yacba.py --model gpt-4o
```

---

### Issue: "Model not found" or "Invalid model" errors

**Symptoms**:
```
Error: Model 'gpt-5' not found
Error: Invalid model identifier
```

**Causes**:
- Typo in model name
- Wrong framework prefix
- Model not available in region
- Outdated model name

**Solutions**:

1. **Check model format**:
```bash
# Correct formats:
--model "gpt-4o"                              # OpenAI (default)
--model "openai:gpt-4o"                       # OpenAI (explicit)
--model "anthropic:claude-3-5-sonnet-20241022"  # Anthropic
--model "litellm:gemini/gemini-2.5-flash"     # Google via LiteLLM
--model "ollama:llama2:7b"                    # Ollama
--model "bedrock:anthropic.claude-3-sonnet-20240229-v1:0"  # AWS Bedrock
```

2. **Verify model availability**:
```bash
# Test with known working model
python code/yacba.py --model "gpt-4o" --headless --initial-message "test"
```

3. **Check provider documentation**:
- OpenAI: https://platform.openai.com/docs/models
- Anthropic: https://docs.anthropic.com/claude/docs/models-overview
- LiteLLM: https://docs.litellm.ai/docs/providers

---

### Issue: Application hangs or freezes

**Symptoms**:
- No response after sending message
- Cursor stuck
- No error messages

**Causes**:
- Network timeout
- Model processing long request
- Deadlock in async code
- Tool execution hanging

**Solutions**:

1. **Cancel operation**:
```
Press Alt+C (or Ctrl+C)
```

2. **Check network connectivity**:
```bash
# Test API endpoint
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

3. **Increase timeout** (if supported):
```bash
# Set timeout environment variable (if available)
export YACBA_TIMEOUT=120
```

4. **Enable debug logging**:
```bash
export LOGURU_LEVEL=DEBUG
python code/yacba.py --model gpt-4o
# Look for where it hangs
```

5. **Test in headless mode**:
```bash
# Simpler mode, easier to debug
python code/yacba.py --model gpt-4o --headless --initial-message "test"
```

---

## Configuration Problems

### Issue: Configuration not loading

**Symptoms**:
```
Warning: No configuration file found
Using defaults only
```

**Causes**:
- Config file in wrong location
- Wrong file format
- Syntax errors in config file

**Solutions**:

1. **Check config file locations**:
```bash
# YACBA looks in these locations (in order):
ls -la ./.yacba/config.yaml      # Project-specific
ls -la ~/.yacba/config.yaml      # User-wide
```

2. **Create config directory**:
```bash
mkdir -p ~/.yacba
```

3. **Initialize sample config**:
```bash
python code/yacba.py --init-config ~/.yacba/config.yaml
```

4. **Validate YAML syntax**:
```bash
# Use Python to validate
python -c "import yaml; yaml.safe_load(open('~/.yacba/config.yaml'))"

# Or use online validator: https://www.yamllint.com/
```

5. **Test with explicit config file**:
```bash
python code/yacba.py --config-file ~/.yacba/config.yaml --show-config
```

---

### Issue: Profile not found

**Symptoms**:
```
Error: Profile 'production' not found in configuration
```

**Causes**:
- Typo in profile name
- Profile not defined in config file
- Wrong config file loaded

**Solutions**:

1. **List available profiles**:
```bash
python code/yacba.py --list-profiles
```

2. **Check profile definition**:
```yaml
# ~/.yacba/config.yaml
profiles:
  development:  # ← Profile name must match
    model: "gpt-4o"
  production:   # ← Check spelling
    model: "claude-3-5-sonnet"
```

3. **Use default profile**:
```bash
# Don't specify --profile, uses 'default' or 'default_profile'
python code/yacba.py --model gpt-4o
```

4. **Override with CLI**:
```bash
# CLI args override profile settings
python code/yacba.py --profile production --model gpt-4o
```

---

### Issue: Configuration precedence confusion

**Symptoms**:
- Expected value not being used
- CLI argument ignored
- Profile setting not applied

**Causes**:
- Misunderstanding precedence order
- Value set in multiple places

**Solutions**:

1. **Understand precedence** (lowest to highest):
```
1. Default values (ARGUMENT_DEFAULTS)
2. Environment variables (YACBA_MODEL_ID, etc.)
3. Discovered config files (~/.yacba/config.yaml)
4. --config-file (explicit override)
5. CLI arguments (highest priority)
```

2. **Check resolved configuration**:
```bash
python code/yacba.py --show-config
# Shows final merged configuration
```

3. **Test precedence**:
```bash
# Set in multiple places
export YACBA_MODEL_ID="gpt-3.5-turbo"  # Priority 2
# ~/.yacba/config.yaml has model: "gpt-4"  # Priority 3
python code/yacba.py --model "gpt-4o" --show-config  # Priority 5 (wins)
# Should show: model: 'gpt-4o'
```

4. **Clear environment variables**:
```bash
unset YACBA_MODEL_ID
unset YACBA_SYSTEM_PROMPT
unset YACBA_SESSION_NAME
```

---

## Tool Loading Issues

> **Note**: Tool loading is handled by strands-agent-factory. Most tool issues should be reported there.  
> See [strands-agent-factory tool troubleshooting](https://github.com/JBarmentlo/strands-agent-factory#tools) for tool-specific issues.


### Issue: Tools not loading

**Symptoms**:
```
Warning: No tools found
Tool discovery found 0 tools
```

**Causes**:
- Wrong directory path
- No tool config files in directory
- Invalid tool config format
- Permission issues

**Solutions**:

1. **Verify directory exists**:
```bash
ls -la /path/to/tools/
```

2. **Check for config files**:
```bash
# YACBA looks for *.json and *.yaml files
ls /path/to/tools/*.{json,yaml}
```

3. **Validate tool config format**:
```json
{
  "tools": [
    {
      "type": "python_function",
      "module": "my_tools.calculator",
      "config": {
        "functions": ["add", "multiply"]
      }
    }
  ]
}
```

4. **Test tool discovery**:
```bash
export LOGURU_LEVEL=DEBUG
python code/yacba.py --tool-configs-dir /path/to/tools --show-config
# Check debug output for tool discovery
```

5. **Check permissions**:
```bash
# Ensure files are readable
chmod 644 /path/to/tools/*.json
```

---

### Issue: Tool execution fails

**Symptoms**:
```
Error executing tool 'my_function'
Tool returned error: ...
```

**Causes**:
- Tool function not found
- Import errors in tool module
- Tool function raises exception
- Missing dependencies

**Solutions**:

1. **Enable tool use visibility**:
```bash
python code/yacba.py --show-tool-use
# Shows detailed tool execution info
```

2. **Test tool function directly**:
```python
# Test in Python REPL
from my_tools.calculator import add
result = add(2, 3)
print(result)  # Should work
```

3. **Check tool module path**:
```json
{
  "tools": [{
    "type": "python_function",
    "module": "my_tools.calculator",  # Must be importable
    "config": {
      "package_path": "src/",  # Optional: add to sys.path
      "base_path": "/project/root"  # Optional: base directory
    }
  }]
}
```

4. **Verify dependencies**:
```bash
# If tool requires packages
pip install -r tool_requirements.txt
```

---

### Issue: MCP server not starting

**Symptoms**:
```
Error: MCP server failed to start
Connection refused
```

**Causes**:
- Server command not found
- Port already in use
- Server crashes on startup
- Missing environment variables

**Solutions**:

1. **Test server command manually**:
```bash
# Run server command from config
python -m my_mcp_server --port 8080
# Should start without errors
```

2. **Check port availability**:
```bash
# Check if port is in use
lsof -i :8080
netstat -an | grep 8080
```

3. **Verify server config**:
```json
{
  "tools": [{
    "type": "mcp_server",
    "config": {
      "command": ["python", "-m", "my_mcp_server"],
      "args": ["--port", "8080"],
      "env": {
        "API_KEY": "${MY_API_KEY}"  # Ensure env var is set
      }
    }
  }]
}
```

4. **Check server logs**:
```bash
export LOGURU_LEVEL=DEBUG
python code/yacba.py --tool-configs-dir /path/to/tools
# Look for MCP server startup logs
```

---

## Model Connection Problems

> **Note**: LLM provider connections are handled by strands-agent-factory.  
> See [strands-agent-factory provider docs](https://github.com/JBarmentlo/strands-agent-factory#providers) for connection issues.


### Issue: Connection timeout

**Symptoms**:
```
Error: Connection timeout
Failed to connect to API endpoint
```

**Causes**:
- Network issues
- Firewall blocking connection
- API endpoint down
- Proxy configuration

**Solutions**:

1. **Test network connectivity**:
```bash
# Test API endpoint
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

2. **Check firewall**:
```bash
# Ensure outbound HTTPS (443) is allowed
telnet api.openai.com 443
```

3. **Configure proxy** (if needed):
```bash
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="http://proxy.example.com:8080"
```

4. **Try different model/provider**:
```bash
# Test with different provider
python code/yacba.py --model "anthropic:claude-3-5-sonnet"
```

---

### Issue: Rate limit errors

**Symptoms**:
```
Error: Rate limit exceeded
429 Too Many Requests
```

**Causes**:
- Too many requests in short time
- Exceeded API quota
- Shared API key with high usage

**Solutions**:

1. **Wait and retry**:
```bash
# Wait a few minutes
sleep 60
python code/yacba.py --model gpt-4o
```

2. **Check API usage**:
- OpenAI: https://platform.openai.com/usage
- Anthropic: https://console.anthropic.com/settings/usage

3. **Use different model**:
```bash
# Use cheaper/faster model
python code/yacba.py --model "gpt-3.5-turbo"
```

4. **Implement retry logic** (if available):
```bash
# Some providers support automatic retry
# Check provider documentation
```

---

### Issue: Invalid API response

**Symptoms**:
```
Error: Invalid response from API
JSON decode error
Unexpected response format
```

**Causes**:
- API endpoint changed
- Provider outage
- Malformed request
- Version mismatch

**Solutions**:

1. **Check provider status**:
- OpenAI: https://status.openai.com/
- Anthropic: https://status.anthropic.com/

2. **Update dependencies**:
```bash
pip install --upgrade strands-agent-factory litellm
```

3. **Test with minimal request**:
```bash
python code/yacba.py --model gpt-4o --headless --initial-message "test"
```

4. **Enable debug logging**:
```bash
export LOGURU_LEVEL=DEBUG
python code/yacba.py --model gpt-4o
# Check request/response in logs
```

---

## File Processing Issues

### Issue: File not found

**Symptoms**:
```
Error: File not found: /path/to/file.txt
File does not exist
```

**Causes**:
- Wrong file path
- Typo in filename
- Relative path issue
- Permission denied

**Solutions**:

1. **Verify file exists**:
```bash
ls -la /path/to/file.txt
```

2. **Use absolute path**:
```bash
python code/yacba.py --files "/absolute/path/to/file.txt"
```

3. **Check current directory**:
```bash
pwd  # Where are you running from?
ls file.txt  # Is file in current directory?
```

4. **Use glob pattern**:
```bash
python code/yacba.py --files "*.txt"  # All .txt files in current dir
python code/yacba.py --files "data/*.json"  # All .json in data/
```

---

### Issue: File format not supported

**Symptoms**:
```
Error: Unsupported file format
Cannot process file type
```

**Causes**:
- Unsupported file extension
- Corrupted file
- Wrong mimetype specified

**Solutions**:

1. **Check supported formats**:
```
Supported: PDF, DOC, DOCX, CSV, JSON, YAML, Markdown, TXT, Images
```

2. **Specify mimetype explicitly**:
```bash
python code/yacba.py --files "file.dat" "text/plain"
```

3. **Convert file format**:
```bash
# Convert to supported format
pandoc input.rtf -o output.txt
```

4. **Check file integrity**:
```bash
file /path/to/file.pdf  # Should show "PDF document"
```

---

### Issue: File too large

**Symptoms**:
```
Error: File exceeds maximum size
File too large to process
```

**Causes**:
- File exceeds model context limit
- File exceeds upload limit
- Memory constraints

**Solutions**:

1. **Check file size**:
```bash
ls -lh /path/to/file.txt
du -h /path/to/file.txt
```

2. **Split large file**:
```bash
# Split into smaller chunks
split -l 1000 large_file.txt chunk_
```

3. **Increase max files limit**:
```bash
python code/yacba.py --max-files 50
```

4. **Use summarization**:
```bash
# Enable summarization for large contexts
python code/yacba.py --conversation-manager summarizing
```

---

## Session Management Problems

### Issue: Session not saving

**Symptoms**:
```
Warning: Session not saved
Session persistence disabled
```

**Causes**:
- No session name specified
- Sessions directory not writable
- Disk full

**Solutions**:

1. **Specify session name**:
```bash
python code/yacba.py --session my-session
```

2. **Check sessions directory**:
```bash
ls -la ~/.yacba/sessions/
# Should be writable
```

3. **Create sessions directory**:
```bash
mkdir -p ~/.yacba/sessions
chmod 755 ~/.yacba/sessions
```

4. **Check disk space**:
```bash
df -h ~
```

---

### Issue: Cannot load session

**Symptoms**:
```
Error: Session 'my-session' not found
Failed to load session
```

**Causes**:
- Session doesn't exist
- Typo in session name
- Corrupted session file

**Solutions**:

1. **List available sessions**:
```bash
ls ~/.yacba/sessions/
```

2. **Check session file**:
```bash
cat ~/.yacba/sessions/my-session.json
# Should be valid JSON
```

3. **Create new session**:
```bash
python code/yacba.py --session new-session
```

4. **Recover from backup** (if available):
```bash
cp ~/.yacba/sessions/my-session.json.bak ~/.yacba/sessions/my-session.json
```

---

## Performance Issues

### Issue: Slow response times

**Symptoms**:
- Long wait for responses
- Laggy interface
- High CPU usage

**Causes**:
- Large context window
- Complex tool execution
- Network latency
- Model processing time

**Solutions**:

1. **Use faster model**:
```bash
python code/yacba.py --model "gpt-3.5-turbo"  # Faster than GPT-4
python code/yacba.py --model "litellm:gemini/gemini-2.5-flash"  # Very fast
```

2. **Enable sliding window**:
```bash
python code/yacba.py --conversation-manager sliding_window --window-size 20
```

3. **Reduce context**:
```bash
# Smaller window
python code/yacba.py --window-size 10

# Enable truncation
python code/yacba.py  # --no-truncate-results is off by default
```

4. **Check network latency**:
```bash
ping api.openai.com
```

---

### Issue: High memory usage

**Symptoms**:
- System slowdown
- Out of memory errors
- Swap usage high

**Causes**:
- Large conversation history
- Many files uploaded
- Memory leak

**Solutions**:

1. **Clear conversation**:
```
/clear  # In interactive mode
```

2. **Limit files**:
```bash
python code/yacba.py --max-files 5
```

3. **Use summarization**:
```bash
python code/yacba.py --conversation-manager summarizing
```

4. **Restart application**:
```bash
# Exit and restart
/quit
python code/yacba.py --session my-session  # Resume
```

---

## Debugging Techniques

### Enable Verbose Logging

```bash
# Debug level
export LOGURU_LEVEL=DEBUG
python code/yacba.py --model gpt-4o

# Trace level (very verbose)
export LOGURU_LEVEL=TRACE
python code/yacba.py --model gpt-4o

# Log to file
export LOGURU_LEVEL=DEBUG
python code/yacba.py --model gpt-4o 2>&1 | tee yacba.log
```

### Use Python Debugger

```bash
# Run with pdb
python -m pdb code/yacba.py --model gpt-4o

# Set breakpoint in code
import pdb; pdb.set_trace()
```

### Test Components Individually

```python
# Test configuration
PYTHONPATH=code python -c "
from config import parse_config
import sys
sys.argv = ['test', '--model', 'gpt-4o', '--show-config']
config = parse_config()
"

# Test adapter
PYTHONPATH=code python -c "
from config import parse_config
from adapters.strands_factory import YacbaToStrandsConfigConverter
import sys
sys.argv = ['test', '--model', 'gpt-4o']
config = parse_config()
converter = YacbaToStrandsConfigConverter(config)
strands_config = converter.convert()
print('✓ Conversion successful')
"
```

### Check Dependencies

```bash
# List installed packages
pip list

# Check specific package
pip show strands-agent-factory

# Verify versions
pip list | grep -E "strands|repl|profile"
```

### Validate Configuration Files

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('~/.yacba/config.yaml'))"

# Validate JSON syntax
python -c "import json; json.load(open('tool_config.json'))"

# Show resolved config
python code/yacba.py --show-config
```

---

## Getting Help

### Before Asking for Help

1. **Check this troubleshooting guide**
2. **Enable debug logging** and review output
3. **Test with minimal configuration**
4. **Verify dependencies are installed**
5. **Check for known issues** in documentation

### Information to Provide

When asking for help, include:

1. **YACBA version**:
```bash
git describe --tags  # If using git
cat VERSION  # If available
```

2. **Python version**:
```bash
python --version
```

3. **Dependency versions**:
```bash
pip list | grep -E "strands|repl|profile"
```

4. **Configuration** (sanitized):
```bash
python code/yacba.py --show-config
# Remove sensitive data (API keys, etc.)
```

5. **Error message** (full):
```bash
# Include full error output
python code/yacba.py --model gpt-4o 2>&1 | tee error.log
```

6. **Debug logs**:
```bash
export LOGURU_LEVEL=DEBUG
python code/yacba.py --model gpt-4o 2>&1 | tee debug.log
```

7. **Steps to reproduce**:
```
1. Run: python code/yacba.py --model gpt-4o
2. Type: "hello"
3. Error occurs: ...
```

### Where to Get Help

1. **Documentation**:
   - [API Documentation](API.md)
   - [Architecture Documentation](ARCHITECTURE.md)
   - [Configuration Guide](../README.CONFIG.md)

2. **GitHub Issues**:
   - Search existing issues
   - Create new issue with template

3. **Community**:
   - Discussion forums
   - Chat channels

---

## Common Error Messages

### "Configuration parsing failed"

**Cause**: Invalid configuration syntax or values

**Solution**: Run `--show-config` to see where parsing fails, validate YAML/JSON syntax

---

### "Agent initialization failed"

**Cause**: Problem creating agent (API keys, model, tools)

**Solution**: Check API keys, test with minimal config, enable debug logging

---

### "Tool loading failed"

**Cause**: Invalid tool configuration or missing dependencies

**Solution**: Validate tool config format, check module imports, verify dependencies

---

### "Session persistence error"

**Cause**: Cannot read/write session files

**Solution**: Check directory permissions, verify disk space, validate session file format

---

### "Context window exceeded"

**Cause**: Conversation too long for model's context limit

**Solution**: Enable conversation management, use summarization, clear history

---

## Best Practices

### Configuration

1. Use profiles for different environments
2. Keep sensitive data in environment variables
3. Validate configuration with `--show-config`
4. Document custom configurations

### Debugging

1. Start with minimal configuration
2. Enable debug logging early
3. Test components individually
4. Keep logs for analysis

### Performance

1. Use appropriate models for tasks
2. Enable conversation management
3. Limit file uploads
4. Monitor resource usage

### Maintenance

1. Keep dependencies updated
2. Backup session files
3. Clean old sessions periodically
4. Monitor API usage

---

## See Also

- [API Documentation](API.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [Configuration Guide](../README.CONFIG.md)
- [Model Configuration Guide](../README.MODEL_CONFIG.md)

---

## Getting Help

### Where to Report Issues

**YACBA Issues** ([GitHub Issues](https://github.com/your-username/yacba/issues)):
- CLI argument parsing problems
- Configuration file loading errors  
- Profile system issues
- Interactive REPL bugs
- Tab completion not working
- File glob processing errors

**strands-agent-factory Issues** ([GitHub Issues](https://github.com/JBarmentlo/strands-agent-factory/issues)):
- LLM provider connection errors
- Tool loading/execution failures
- Tool configuration format issues
- A2A (Agent-to-Agent) setup problems
- Conversation management bugs
- Session persistence errors

**Not sure which?**
- If it's about the CLI/config → YACBA
- If it's about agents/tools/LLMs → strands-agent-factory

### Before Reporting

1. **Check existing issues** in the appropriate repository
2. **Enable debug logging**: `export LOGURU_LEVEL=DEBUG`
3. **Test with minimal config**: Remove customizations
4. **Verify versions**: Check strands-agent-factory and repl-toolkit versions

### Include in Bug Reports

**For YACBA issues**:
- Python version
- YACBA version (git commit hash)
- Full command that failed
- Output of `--show-config`
- Debug logs (`LOGURU_LEVEL=DEBUG`)
- Operating system

**For strands-agent-factory issues**:
- See [strands-agent-factory contributing guide](https://github.com/JBarmentlo/strands-agent-factory/blob/main/CONTRIBUTING.md)

### Community Support

- **Discussions**: GitHub Discussions for questions
- **Documentation**: Check all relevant docs first
- **Examples**: Look at sample configs in the repository

---

## Related Documentation

- [Main README](../README.md) - Feature overview
- [API Documentation](API.md) - YACBA wrapper APIs
- [Architecture](ARCHITECTURE.md) - System design
- [Completion System](COMPLETION_SYSTEM.md) - Tab completion
- **[strands-agent-factory Docs](https://github.com/JBarmentlo/strands-agent-factory)** - Core agent features

---

Last Updated: 2025-01-06
