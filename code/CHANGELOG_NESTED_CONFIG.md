# Changelog: Nested Configuration Refactoring

**Version**: TBD  
**Date**: 2024-12-XX  
**Type**: BREAKING CHANGE

## Summary

YACBA configuration has been refactored to use nested structure with `cli_nested` from dataclass-args. This is a **breaking change** that requires users to migrate their configuration files.

## What Changed

### Configuration Structure

Configuration files now use nested sections:

```yaml
# OLD (no longer supported)
model_string: "gpt-4"
session_name: "my-session"
headless: false

# NEW (required)
agent:
  model: "gpt-4"
  session_id: "my-session"
repl:
  headless: false
```

### Environment Variables

Environment variables now use nested prefixes:

```bash
# OLD (no longer supported)
export YACBA_MODEL_STRING="gpt-4"
export YACBA_HEADLESS="true"

# NEW (required)
export YACBA_AGENT_MODEL="gpt-4"
export YACBA_REPL_HEADLESS="true"
```

### Field Renames

| Old Name | New Name | Section |
|----------|----------|---------|
| `model_string` | `model` | `agent` |
| `session_name` | `session_id` | `agent` |
| `tool_configs_dir` | `tool_config_paths` | `agent` |

### Code Removed

- **~200 lines**: `_map_flat_to_nested()` - backward compatibility mapping
- **~50 lines**: `_load_and_map_config_file()` - old config file support
- **~30 lines**: Backward compatibility properties (session_name, model_string)
- **~80 lines**: Flat-to-nested environment variable mapping

**Total**: ~360 lines of backward compatibility code removed

## Why This Change

1. **Type Safety**: `config.agent` IS `AgentFactoryConfig` (no converter)
2. **Maintainability**: No duplicate field definitions or mappings
3. **Clarity**: Clear separation between agent and REPL configuration
4. **Consistency**: Matches strands-agent-factory structure directly

## Migration Required

**All users must migrate their configuration files before upgrading.**

See `MIGRATION_NESTED_CONFIG.md` for detailed migration instructions.

### Quick Migration

1. **Profile configs** (`.yacba/config.yaml`):
   ```bash
   # Backup old config
   cp ~/.yacba/config.yaml ~/.yacba/config.yaml.backup
   
   # Generate new sample
   yacba --init-config ~/.yacba/config.yaml
   
   # Manually migrate your settings to nested structure
   ```

2. **Environment variables**:
   ```bash
   # Update your .bashrc, .zshrc, etc.
   # OLD: export YACBA_MODEL_STRING="gpt-4"
   # NEW: export YACBA_AGENT_MODEL="gpt-4"
   ```

3. **Test**:
   ```bash
   yacba --show-config
   ```

## Error Messages

If you see these errors, migration is required:

```
ERROR: profile_config_not_nested
  Profile config must use nested structure. See MIGRATION_NESTED_CONFIG.md
```

```
ValueError: Config file must use nested structure with 'agent' and/or 'repl' sections.
  See MIGRATION_NESTED_CONFIG.md for migration guide.
```

## CLI Arguments

**No changes** - all CLI arguments work exactly as before:
- `-m` / `--model`
- `-s` / `--system-prompt`
- `-H` / `--headless`
- `-f` / `--file-paths`
- `-t` / `--tool-config-paths`
- etc.

## Benefits

- **300+ lines of code removed**
- Direct type-safe access to AgentFactoryConfig
- No configuration converter needed
- Clearer configuration structure
- Better error messages

## Related Changes

- **strands-agent-factory**: Updated to accept `List[List[str]]` for `file_paths` (instead of tuples)
- **dataclass-args**: Fixed --config handling with base_configs

## Documentation

- `MIGRATION_NESTED_CONFIG.md` - Detailed migration guide
- `README.md` - Updated with new config examples
- `ARCHITECTURE.md` - Removed converter section

## Rollback

If you need to rollback:

1. Checkout previous version
2. Restore old config files from backup
3. File an issue describing the problem

## Support

If you encounter migration issues:

1. Check `MIGRATION_NESTED_CONFIG.md`
2. Run `yacba --show-config` to see current config
3. File an issue with your config file (redact sensitive values)
