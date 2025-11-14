# Model Configuration

YACBA provides flexible model configuration through JSON configuration files and command-line overrides, allowing you to fine-tune model parameters like temperature, max_tokens, and more without modifying code.

## Configuration Methods

### 1. JSON Configuration Files

Create JSON files containing model parameters:

```bash
# Use a pre-configured model setup
yacba --model-config sample-model-configs/openai-gpt4.json
```

**Note**: Configuration files are loaded via YAML parser, so both JSON and YAML formats work (JSON is valid YAML).

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

Use the `--mc` flag (short for `--model-config` property override) to set individual configuration properties:

```bash
# Simple properties
yacba --mc temperature:0.8 --mc max_tokens:2048

# Nested properties (dot notation)
yacba --mc response_format.type:json_object

# Array indexing
yacba --mc safety_settings[0].threshold:BLOCK_LOW_AND_ABOVE
```

### 3. Combined Configuration

Combine JSON files with command-line overrides (overrides take precedence):

```bash
# Load base config and override specific values
yacba --model-config base-config.json --mc temperature:0.9 --mc max_tokens:1024
```

## Command-Line Syntax

### Model Configuration
- `--model-config <path>`: Load configuration from JSON file
- `--mc <property:value>`: Override individual property (can be used multiple times)

### Summarization Model Configuration
- `--summarization-model-config <path>`: Load summarization model config from JSON file
- `--smc <property:value>`: Override summarization model property (can be used multiple times)

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

Quoted strings are preserved as strings. Unquoted values are inferred by type.

## Framework-Specific Examples

### OpenAI/GPT Models

```bash
# GPT-4 with JSON mode
yacba -m openai:gpt-4 \
  --mc temperature:0.7 \
  --mc response_format.type:json_object \
  --mc max_tokens:4096

# GPT-3.5 with custom stop sequences  
yacba -m openai:gpt-3.5-turbo \
  --mc temperature:0.5 \
  --mc "stop:[\"END\",\"STOP\"]"
```

### Anthropic Claude

```bash
# Claude with specific parameters
yacba -m anthropic:claude-3-sonnet-20240229 \
  --mc max_tokens:4096 \
  --mc temperature:0.8 \
  --mc top_k:5

# Claude via Bedrock
yacba -m bedrock:anthropic.claude-3-sonnet-20240229-v1:0 \
  --mc max_tokens:4096 \
  --mc anthropic_version:bedrock-2023-05-31
```

### Google Gemini

```bash
# Gemini with safety settings
yacba -m litellm:gemini/gemini-1.5-pro \
  --mc temperature:0.7 \
  --mc top_k:40 \
  --mc safety_settings[0].category:HARM_CATEGORY_HARASSMENT \
  --mc safety_settings[0].threshold:BLOCK_LOW_AND_ABOVE
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
yacba --model-config sample-model-configs/openai-gpt4.json

# Customize a sample configuration
yacba --model-config sample-model-configs/litellm-gemini.json --mc temperature:0.95
```

## Advanced Configuration Examples

### Research Assistant Setup

```bash
yacba -m openai:gpt-4 \
  --model-config research-assistant.json \
  --mc temperature:0.3 \
  --mc max_tokens:8192 \
  --mc response_format.type:json_object
```

### Creative Writing Setup

```bash
yacba -m openai:gpt-4 \
  --mc temperature:0.9 \
  --mc top_p:0.95 \
  --mc presence_penalty:0.6 \
  --mc frequency_penalty:0.3
```

### Code Analysis Setup

```bash
yacba -m anthropic:claude-3-sonnet-20240229 \
  --mc temperature:0.1 \
  --mc max_tokens:4096
```

## Summarization Model Configuration

Configure the model used for conversation summarization separately:

```bash
# Use different model for summarization
yacba -m openai:gpt-4 \
  --conversation-manager-type summarizing \
  --summarization-model "litellm:gemini/gemini-1.5-flash" \
  --summarization-model-config summary-config.json

# Override summarization model properties
yacba -m openai:gpt-4 \
  --conversation-manager-type summarizing \
  --summarization-model "litellm:gemini/gemini-1.5-flash" \
  --smc temperature:0.3 \
  --smc max_tokens:2000
```

## Using in Profile Configuration

Model configuration can be specified in profile config files:

```yaml
profiles:
  development:
    model_string: "openai:gpt-4"
    model_config:
      temperature: 0.7
      max_tokens: 4096
      top_p: 0.95
    
  production:
    model_string: "openai:gpt-4"
    model_config:
      temperature: 0.3
      max_tokens: 8192
      response_format:
        type: json_object
```

Or reference a JSON file:

```yaml
profiles:
  development:
    model_string: "openai:gpt-4"
    # Note: YACBA loads model_config as dict from profile
    # To use a JSON file, specify in CLI: --model-config path/to/file.json
```

## Configuration Validation

YACBA validates configuration files and overrides:

- **Syntax**: Configuration files must be valid JSON or YAML
- **Type Safety**: Values are validated and converted appropriately
- **Path Validation**: Property paths are checked for syntax errors
- **Array Bounds**: Array indices are validated when possible

Error messages provide clear guidance when configuration issues are detected:

```bash
$ yacba --mc "invalid_format"
Error: Invalid property override format: 'invalid_format'. Expected format: 'property.path:value'

$ yacba --mc "array[invalid]:value"  
Error: Invalid array index 'invalid' in property path: array[invalid]
```

## Implementation Details

- Configuration parsing: `code/utils/model_config_parser.py`
- File format: JSON or YAML (loaded via YAML parser)
- Property paths: Dot notation for nesting, brackets for arrays
- Type inference: Automatic conversion based on value format
- Dict fields: `model_config` and `summarization_model_config` in YacbaConfig

## Tips

1. **Start with sample configs**: Use provided samples as templates
2. **Test with --show-config**: Verify configuration is applied correctly
3. **Use JSON for consistency**: While YAML works, samples use JSON
4. **Quote complex values**: Use quotes for strings that might be misinterpreted
5. **Combine approaches**: Load base config from file, override specific values via CLI

## Common Parameters by Provider

### OpenAI
- `temperature` (0.0-2.0): Sampling temperature
- `max_tokens`: Maximum tokens in response
- `top_p` (0.0-1.0): Nucleus sampling
- `presence_penalty` (-2.0-2.0): Penalize new topics
- `frequency_penalty` (-2.0-2.0): Penalize repetition
- `response_format`: `{"type": "text"}` or `{"type": "json_object"}`
- `stop`: String or array of stop sequences

### Anthropic (Claude)
- `max_tokens`: Maximum tokens (required)
- `temperature` (0.0-1.0): Sampling temperature
- `top_p` (0.0-1.0): Nucleus sampling
- `top_k`: Only sample from top K options
- `stop_sequences`: Array of stop sequences

### Google (Gemini)
- `temperature` (0.0-2.0): Sampling temperature
- `max_tokens`: Maximum output tokens
- `top_p` (0.0-1.0): Nucleus sampling
- `top_k`: Top-k sampling
- `safety_settings`: Array of safety configurations

### AWS Bedrock (Claude)
- Same as Anthropic, plus:
- `anthropic_version`: API version (e.g., "bedrock-2023-05-31")
- `boto_client_config`: AWS client configuration

Refer to your LLM provider's documentation for complete parameter lists and valid ranges.
