# Tag System Documentation

## Overview

The Tag System provides conversation position bookmarking for YACBA. Tags allow you to mark specific points in a conversation and return to them later, enabling non-linear conversation exploration and easy rollback of mistakes.

## Key Features

- **Position Bookmarking**: Mark any point in your conversation with a memorable name
- **Smart Undo**: Undo by user message count or jump directly to a tagged position
- **Hash Validation**: Tags validate against message content to detect stale references
- **Automatic Cleanup**: Invalid tags are automatically detected and removed
- **Session Integration**: Special `__session_start__` tag marks conversation beginning

## Commands

### `/tag [name] [position]`

Create a conversation position tag.

**Usage:**
```
/tag                    - List all tags (same as /tags)
/tag checkpoint         - Tag current position as "checkpoint"
/tag work 42            - Tag position 42 as "work"
```

**Examples:**
```
> /tag experiment
Tag 'experiment' created at position 15

> /tag baseline 0
Tag 'baseline' created at position 0
```

### `/undo <N|tag>`

Undo conversation messages.

**Usage:**
```
/undo                   - Undo last user input message (default: 1)
/undo 3                 - Undo last 3 user input messages
/undo checkpoint        - Restore to tagged position "checkpoint"
/undo 100               - Clear all messages (if < 100 user messages exist)
```

**Behavior:**
- `undo N` counts **user input messages only** (excludes tool results)
- If N exceeds available user messages, clears entire conversation
- Removes any tags that become out of scope
- Recreates `__session_start__` tag if conversation cleared

**Examples:**
```
> /undo 2
Removed last 2 user messages (5 total messages)
Tags removed: recent_work

> /undo baseline
Restored to tag 'baseline' (removed 23 messages)

> /undo experiment
Error: Tag 'experiment' is no longer valid (hash mismatch). Tag removed.
```

### `/tags`

List all tags with validation status.

**Usage:**
```
/tags                   - Show all conversation position tags
```

**Output:**
```
Current tags:
  [SPECIAL] __session_start__ → position    0 (10:30:00)
  checkpoint                  → position    5 (10:31:15)
  experiment                  → position   12 (10:32:45)
  work                        → position   20 INVALIDATED: Position 20 out of range (0-15)

Removed 1 invalid tag(s): work
```

Second call after invalid tags removed:
```
Current tags:
  [SPECIAL] __session_start__ → position    0 (10:30:00)
  checkpoint                  → position    5 (10:31:15)
  experiment                  → position   12 (10:32:45)
```

### `/clear`

Clear conversation and reset tags.

**Behavior:**
- Clears all messages
- Removes all user-defined tags
- Recreates `__session_start__` tag at position 0

## Understanding User Messages vs Tool Results

The undo system distinguishes between **user input messages** and **tool result messages**:

### User Input Messages
Messages you type directly:
```json
{
  "role": "user",
  "content": [{"text": "Hello, please help me"}]
}
```

### Tool Result Messages
System-generated responses from tool execution:
```json
{
  "role": "user",
  "content": [{
    "toolResult": {
      "toolUseId": "123",
      "content": [...]
    }
  }]
}
```

**Important:** `/undo N` counts **only user input messages**, not tool results.

## Tag Validation

Tags are validated lazily (on use) using message content hashes.

### Why Validation?

Conversation managers (sliding window, summarization) can modify message arrays. Tags need to detect when they point to:
- Removed messages (out of range)
- Replaced messages (hash mismatch)
- Moved messages (different content at position)

### How It Works

1. **On Tag Creation**: Compute SHA256 hash of message content
2. **On Tag Use**: Recompute hash and compare
3. **If Invalid**: Remove tag and report error

### Validation States

**Valid Tag:**
```
  checkpoint → position 5 (10:31:15)
```

**Invalid Tag (out of range):**
```
  work → position 20 INVALIDATED: Position 20 out of range (0-15)
```

**Invalid Tag (hash mismatch):**
```
  old_work → position 8 INVALIDATED: Message at position 8 has changed (hash mismatch)
```

## Special Tags

### `__session_start__`

Automatically created special tag marking conversation beginning.

**Properties:**
- Created at position 0 on session start
- **Never invalidated**: Always valid regardless of content changes (positional marker only)
- Recreated on `/clear` or when `/undo N` clears all messages
- Cannot be overwritten by user
- Marked with `[SPECIAL]` in tag listings
- Uses special hash marker `SESSION_START`

## Workflow Examples

### Example 1: Experimental Branching

```bash
# Working on feature
> Implement authentication system

# Tag current state before experiment
> /tag stable

# Try experimental approach
> Try using OAuth2 instead

# Doesn't work, revert to stable state
> /undo stable
Restored to tag 'stable' (removed 4 messages)

# Try different approach
> Use JWT tokens instead
```

### Example 2: Multi-step Recovery

```bash
# Create checkpoints during long task
> Step 1: Design database schema
> /tag step1

> Step 2: Implement API endpoints
> /tag step2

> Step 3: Add authentication
> /tag step3

# Mistake in step 3, go back
> /undo step2
Restored to tag 'step2' (removed 6 messages)
Tags removed: step3

# Redo step 3 correctly
> Step 3: Add authentication (correct approach)
```

### Example 3: Undo by Count

```bash
# Made several mistakes
> Wrong command 1
> Wrong command 2
> Wrong command 3

# Undo last 3 user messages
> /undo 3
Removed last 3 user messages (9 total messages)

# Start fresh
> Correct command
```

## Technical Details

### Tag Structure

```python
@dataclass
class Tag:
    name: str              # User-defined or auto-generated name
    position: int          # Absolute message array index
    message_hash: str      # SHA256 hash (16 chars) of message content
    timestamp: datetime    # When tag was created
    is_special: bool       # Whether this is a system tag
```

### Hash Computation

```python
def compute_message_hash(message: Message) -> str:
    """Compute stable hash of message content."""
    message_str = json.dumps(message["content"], sort_keys=True)
    hash_obj = hashlib.sha256(message_str.encode())
    return hash_obj.hexdigest()[:16]
```

### User Input Detection

```python
def is_user_input_message(message: Message) -> bool:
    """Check if message is user input (not tool result)."""
    if message["role"] != "user":
        return False
    
    # Check for toolResult blocks
    for block in message.get("content", []):
        if "toolResult" in block:
            return False
    
    return True
```

## Edge Cases

### Tagging End of Conversation

You can tag at `position == len(messages)` (after last message):

```python
messages: [m0, m1, m2]  # 3 messages
/tag end 3              # Tag position 3 (after last message)
```

Special hash marker: `END_OF_CONVERSATION`

### Undo Beyond Available Messages

```bash
# Only 3 user messages in conversation
> /undo 100
Removed all 3 user messages (10 total messages)
Tags removed: all_tags
```

Equivalent to `/clear` but via undo mechanism.

### Conversation Manager Interactions

**Sliding Window** removes old messages:
```
Before: [m0, m1, m2, m3, m4, m5]
Tag: work → position 3

After sliding window: [m3, m4, m5]
# m3 now at position 0

/tags
work → position 3 INVALIDATED: Message at position 3 has changed (hash mismatch)
```

**Summarization** replaces messages:
```
Before: [m0, m1, m2, m3, m4, m5]
Tag: checkpoint → position 2

After summarization: [summary, m4, m5]

/tags
checkpoint → position 2 INVALIDATED: Position 2 out of range (0-3)
```

## Best Practices

1. **Tag Before Experiments**: Create tag before trying risky operations
2. **Use Descriptive Names**: `experiment_oauth` better than `tag1`
3. **Check Tags Regularly**: Run `/tags` to see what's still valid
4. **Clean Start**: Use `/clear` when starting completely new topic
5. **Undo Small**: Prefer `undo 2` over `undo 20` for fine control

## Implementation Status

**Completed:**
- ✅ Core TagManager with hash validation
- ✅ `/tag` command (create and list)
- ✅ `/undo N` (by user message count)
- ✅ `/undo tag` (restore to tagged position)
- ✅ `/tags` command (list with validation)
- ✅ `/clear` integration with tags
- ✅ Special `__session_start__` tag
- ✅ Automatic invalid tag removal
- ✅ Unit tests (24 tests, all passing)

**Future Enhancements:**
- Tag persistence across sessions
- Tag export/import
- Tag history/versioning
- Anonymous tag generation
- Tag renaming

## Testing

Run tag system tests:
```bash
python -m pytest code/tests/unit/test_tag_manager.py -v
```

All tests should pass (24/24).

## Architecture

```
code/adapters/repl_toolkit/
├── tag_manager.py              # Core TagManager class
├── backend.py                  # YacbaBackend with tag_manager
└── actions/
    ├── tag_actions.py          # /tag, /undo, /tags handlers
    └── session_actions.py      # /clear with tag integration
```

## See Also

- [Session Management](SESSION_MANAGEMENT.md)
- [Conversation Managers](CONVERSATION_MANAGERS.md)
- [Command Reference](COMMANDS.md)
