# Model Configuration

YACBA provides flexible model configuration through JSON files and command-line overrides, allowing you to fine-tune model parameters like temperature, max_tokens, and more without modifying code.

## Configuration Methods

### 1. JSON Configuration Files

Create JSON files containing model parameters:

```bash
# Use a pre-configured model setup
./yacba --model-config sample-model-configs/openai-gpt4.json
```

**Example configuration files:**

`openai-gpt4.json`:
```json
{
  "temperature": 0.8,
  "max_tokens": 4096,
  "top_p": 0.95,
  "presence_penalty": 0.1,
  "frequency_penalty": 0.0,
  "response_format": {
    "type": "text"
  },
  "stop": null
}
```

`gemini-creative.json`:
```json
{
  "temperature": 0.9,
  "max_tokens": 2048,
  "top_p": 0.95,
  "top_k": 40,
  "safety_settings": [
    {
      "category": "HARM_CATEGORY_HARASSMENT",
      "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    }
  ]
}
```

### 2. Command-Line Overrides

Use the `-c` flag to set individual configuration properties:

```bash
# Simple properties
./yacba -c temperature:0.8 -c max_tokens:2048

# Nested properties (dot notation)
./yacba -c response_format.type:json_object

# Array indexing
./yacba -c safety_settings[0].threshold:BLOCK_LOW_AND_ABOVE
```

### 3. Combined Configuration

Combine JSON files with command-line overrides (overrides take precedence):

```bash
# Load base config and override specific values
./yacba --model-config base-config.json -c temperature:0.9 -c max_tokens:1024
```

## Supported Property Paths

The configuration system supports:

- **Simple properties**: `temperature`, `max_tokens`, `top_p`
- **Nested objects**: `response_format.type`, `usage.prompt_tokens`
- **Array indexing**: `safety_settings[0].category`, `stop[1]`
- **Mixed paths**: `tools[0].function.parameters.type`

## Type Inference

Values are automatically converted to appropriate types:

| Input | Type | Result |
|-------|------|--------|
| `0.8` | float | `0.8` |
| `2048` | integer | `2048` |
| `true` | boolean | `True` |
| `false` | boolean | `False` |
| `null` | null | `None` |
| `"text"` | string | `"text"` |
| `[1,2,3]` | array | `[1, 2, 3]` |
| `{"key":"value"}` | object | `{"key": "value"}` |

## Framework-Specific Examples

### OpenAI/GPT Models

```bash
# GPT-4 with JSON mode
./yacba -m openai:gpt-4 \
  -c temperature:0.7 \
  -c response_format.type:json_object \
  -c max_tokens:4096

# GPT-3.5 with custom stop sequences  
./yacba -m openai:gpt-3.5-turbo \
  -c temperature:0.5 \
  -c stop:[\"END\",\"STOP\"]
```

### Anthropic Claude

```bash
# Claude with specific parameters
./yacba -m anthropic:claude-3-sonnet-20240229 \
  -c max_tokens:4096 \
  -c temperature:0.8 \
  -c top_k:5

# Claude via Bedrock
./yacba -m bedrock:anthropic.claude-3-sonnet-20240229-v1:0 \
  -c max_tokens:4096 \
  -c anthropic_version:bedrock-2023-05-31
```

### Google Gemini

```bash
# Gemini with safety settings
./yacba -m litellm:gemini/gemini-1.5-pro \
  -c temperature:0.7 \
  -c top_k:40 \
  -c safety_settings[0].category:HARM_CATEGORY_HARASSMENT \
  -c safety_settings[0].threshold:BLOCK_LOW_AND_ABOVE
```

## Sample Configuration Files

YACBA includes several pre-configured model setups in `sample-model-configs/`:

- `openai-gpt4.json` - Balanced GPT-4 settings
- `anthropic-claude.json` - Standard Claude configuration  
- `litellm-gemini.json` - Gemini with safety settings
- `bedrock-claude.json` - Claude via AWS Bedrock

Use them directly or as starting points for your own configurations:

```bash
# Use a sample configuration
./yacba --model-config sample-model-configs/openai-gpt4.json

# Customize a sample configuration
./yacba --model-config sample-model-configs/gemini-creative.json -c temperature:0.95
```

## Advanced Configuration Examples

### Research Assistant Setup

```bash
./yacba --model-config research-assistant.json \
  -c temperature:0.3 \
  -c max_tokens:8192 \
  -c response_format.type:json_object
```

### Creative Writing Setup

```bash
./yacba -m openai:gpt-4 \
  -c temperature:0.9 \
  -c top_p:0.95 \
  -c presence_penalty:0.6 \
  -c frequency_penalty:0.3
```

### Code Analysis Setup

```bash
./yacba -m anthropic:claude-3-sonnet-20240229 \
  -c temperature:0.1 \
  -c max_tokens:4096 \
  -c system_prompt:"You are a senior software engineer focused on code quality and security."
```

## Configuration Validation

YACBA validates configuration files and overrides:

- **JSON Syntax**: Configuration files must be valid JSON
- **Type Safety**: Values are validated against expected types
- **Path Validation**: Property paths are checked for syntax errors
- **Array Bounds**: Array indices are validated when possible

Error messages provide clear guidance when configuration issues are detected:

```bash
$ ./yacba -c "invalid_format"
Error: Invalid property override format: 'invalid_format'. Expected format: 'property.path:value'

$ ./yacba -c "array[invalid]:value"  
Error: Invalid array index 'invalid' in property path: array[invalid]
```