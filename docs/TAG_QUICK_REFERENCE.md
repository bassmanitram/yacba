# Tag System Quick Reference

## Commands

```bash
# List tags
/tags

# Create tag at current position
/tag <name>

# Create tag at specific position
/tag <name> <position>

# Undo last user message (default)
/undo

# Undo N user messages
/undo <N>

# Restore to tagged position
/undo <tag>

# Clear conversation (clears tags too)
/clear
```

## Common Workflows

### Save Before Experiment
```bash
/tag stable
<try something risky>
/undo stable              # if it failed
```

### Quick Undo Mistakes
```bash
<made a mistake>
/undo                     # undo last message

<made 3 mistakes>
/undo 3                   # undo last 3 messages
```

### Multi-Step Checkpoints
```bash
<step 1>
/tag step1
<step 2>
/tag step2
<step 3 fails>
/undo step1               # back to step 1
```

## Tag Validation

Tags show `INVALIDATED` if:
- Position no longer exists (conversation manager removed messages)
- Message content changed (hash mismatch)

Invalid tags are automatically removed when `/tags` is run.

## Special Tags

- `__session_start__`: Automatically created at position 0
- Never invalidated (positional marker, not content validator)
- Cannot be overwritten
- Recreated on `/clear`

## Tips

1. Use `/undo` alone to quickly undo last message
2. Tag before experiments: `/tag before_change`
3. Use descriptive names: `/tag experiment_oauth` not `/tag tag1`
4. Check tag status: `/tags` (run twice to clean invalid ones)
5. Undo counts user input only (excludes tool results)
6. `/undo 999` clears all (if fewer than 999 user messages)

## See Full Docs

For complete documentation: `docs/TAG_SYSTEM.md`
