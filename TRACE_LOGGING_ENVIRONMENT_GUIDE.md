# 🔧 Environment Variable Control for Loguru Trace Logging

## Overview

The `custom_handler.py` module now supports environment variable control for trace logging, allowing you to enable trace output for just that module without affecting other parts of the application.

## 🎯 Environment Variables

### Module-Specific Control
```bash
# Enable trace logging ONLY for custom_handler module
export YACBA_TRACE_CUSTOM_HANDLER=1

# Alternative values that work:
export YACBA_TRACE_CUSTOM_HANDLER=true
export YACBA_TRACE_CUSTOM_HANDLER=yes  
export YACBA_TRACE_CUSTOM_HANDLER=on
```

### Global Trace Control
```bash
# Enable trace logging globally (affects all modules)
export YACBA_TRACE_LEVEL=TRACE
```

### Disable Trace Logging
```bash
# Unset the environment variables
unset YACBA_TRACE_CUSTOM_HANDLER
unset YACBA_TRACE_LEVEL

# Or set to false/0
export YACBA_TRACE_CUSTOM_HANDLER=0
export YACBA_TRACE_CUSTOM_HANDLER=false
```

## 🚀 Usage Examples

### Example 1: Module-Specific Tracing
```bash
# Enable trace logging only for custom_handler
export YACBA_TRACE_CUSTOM_HANDLER=1

# Run YACBA - only custom_handler will show trace output
python yacba.py --model gpt-4 -i "Hello world"

# Clean up
unset YACBA_TRACE_CUSTOM_HANDLER
```

### Example 2: One-Time Command
```bash
# Enable trace for just this command
YACBA_TRACE_CUSTOM_HANDLER=1 python yacba.py --model gpt-4 -i "Test message"
```

### Example 3: Global Trace Level
```bash
# Enable trace logging for all modules
export YACBA_TRACE_LEVEL=TRACE

# Run YACBA - all modules with trace statements will output
python yacba.py --model gpt-4 -i "Hello world"

# Clean up
unset YACBA_TRACE_LEVEL
```

### Example 4: Debugging Session
```bash
# Set up debugging environment
export YACBA_TRACE_CUSTOM_HANDLER=1
export YACBA_MODEL_ID=gpt-4

# Run multiple commands with trace enabled
python yacba.py -i "First test"
python yacba.py -i "Second test" 
python yacba.py --headless -i "Headless test"

# Clean up when done
unset YACBA_TRACE_CUSTOM_HANDLER
```

## 📊 Expected Output

### With Trace Enabled
```bash
$ YACBA_TRACE_CUSTOM_HANDLER=1 python yacba.py --model gpt-4 -i "Hello"

[TRACE] custom_handler:__call__:56 - SilentToolUseCallbackHandler.__call__ arguments: {
    'event': {'messageStart': {'role': 'assistant', 'content': 'Hello there!'}}, 
    'timestamp': '2025-01-01T12:00:00Z'
}

[TRACE] custom_handler:__call__:56 - SilentToolUseCallbackHandler.__call__ arguments: {
    'event': {'messageChunk': {'content': 'How can I help you today?'}}, 
    'chunk_id': 'chunk_001'
}

Chatbot: Hello there! How can I help you today?
```

### Without Trace (Default)
```bash
$ python yacba.py --model gpt-4 -i "Hello"

Chatbot: Hello there! How can I help you today?
```

## 🔍 What Gets Traced

When trace logging is enabled, you'll see:

### Message Events
- `messageStart`: When the assistant begins responding
- `messageChunk`: Each piece of the response as it streams
- `messageStop`: When the response is complete

### Tool Events  
- `toolUse`: When a tool is being invoked
- `current_tool_use`: Tool execution status and parameters

### Metadata
- Timestamps
- Event IDs
- Role information
- Content data

## 💡 Best Practices

### Development
```bash
# Use module-specific tracing during development
export YACBA_TRACE_CUSTOM_HANDLER=1
```

### Debugging
```bash
# Combine with other debugging options
export YACBA_TRACE_CUSTOM_HANDLER=1
python yacba.py --show-tool-use --model gpt-4 -i "Debug this"
```

### Production
```bash
# Keep trace logging disabled in production
unset YACBA_TRACE_CUSTOM_HANDLER
unset YACBA_TRACE_LEVEL
```

### CI/CD
```bash
# In scripts, use one-time environment variables
YACBA_TRACE_CUSTOM_HANDLER=1 python test_script.py
```

## 🎛️ Advanced Control

### Conditional Tracing
```bash
# Only trace when debugging specific issues
if [ "$DEBUG_CALLBACK" = "1" ]; then
    export YACBA_TRACE_CUSTOM_HANDLER=1
fi
```

### Script Integration
```bash
#!/bin/bash
# debug_yacba.sh

echo "🔍 Starting YACBA with trace logging..."
export YACBA_TRACE_CUSTOM_HANDLER=1

python yacba.py "$@"

echo "🧹 Cleaning up..."
unset YACBA_TRACE_CUSTOM_HANDLER
```

## 🎉 Benefits

1. **🎯 Precise Control**: Trace only the module you're debugging
2. **🚀 Performance**: No overhead when tracing is disabled
3. **🔧 Flexibility**: Easy to enable/disable via environment
4. **📊 Rich Data**: Complete visibility into callback arguments
5. **🛠️ Developer Friendly**: Works with existing tooling and scripts

This gives you powerful, granular control over trace logging for debugging YACBA's callback handler behavior! 🚀
