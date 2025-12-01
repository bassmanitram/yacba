# Session Doctor - AI Agent Session Analysis and Repair Tool

A comprehensive bash/jq utility for analyzing, diagnosing, and repairing AI agent session message sequences.

## Features

### 1. **Session Statistics** (`stats`)
Provides comprehensive metrics about your session:
- Total message count
- Breakdown by type:
  - User messages (actual user input)
  - Tool results (system-generated responses)
  - Assistant messages (AI responses)
  - Tool uses (AI tool invocations)
- Session duration and timestamps
- Tool use/result balance verification
- Optional verbose mode shows tool usage breakdown

### 2. **Diagnosis** (`diagnose`)
Detects common session integrity issues:
- **Invalid JSON** - Corrupted message files
- **Missing required fields** - Schema violations
- **Message ID mismatches** - Filename doesn't match internal ID
- **Orphaned tool uses** - Tool calls without corresponding results
- **Orphaned tool results** - Results without matching tool calls
- **Sequence violations** - Expected tool result but got something else

### 3. **Rollback** (`rollback`)
Safely removes recent user interactions:
- Rolls back N user messages (text only, not tool results)
- Removes the user message AND all subsequent activity
- Creates automatic backup before deletion
- Shows preview of what will be deleted
- Confirmation prompt (can be skipped with `-y`)

**Use case**: Remove problematic user requests that led to errors

### 4. **Fix** (`fix`)
Automatically repairs common corruptions:
- **Orphaned tool uses**: Removes incomplete tool call sequences
- Removes from first problematic message onwards
- Creates automatic backup before changes
- Confirmation prompt (can be skipped with `-y`)

**Use case**: Session crashed mid-tool-execution, leaving incomplete sequences

### 5. **Backup** (`backup`)
Create timestamped backups:
- Preserves entire message directory
- Organized by session name and timestamp
- Default location: `./session-backups/`

### 6. **List** (`list`)
Quick overview of all messages:
- Shows index, role, content type
- Preview of message content
- Compact table format

### 7. **Validate** (`validate`)
Check structural integrity:
- JSON validity
- Required field presence
- Schema compliance

## Installation

### Dependencies
```bash
# Ubuntu/Debian
sudo apt-get install jq bc

# macOS
brew install jq bc

# Fedora/RHEL
sudo dnf install jq bc
```

### Setup
```bash
# Make executable
chmod +x session-doctor.sh

# Optionally, add to PATH
sudo cp session-doctor.sh /usr/local/bin/session-doctor
```

## Usage

### Basic Syntax
```bash
./session-doctor.sh <command> <session_messages_dir> [options]
```

### Commands

#### Show Statistics
```bash
./session-doctor.sh stats ~/.yacba/strands/sessions/my-session/agents/agent/messages

# With verbose tool breakdown
./session-doctor.sh stats ~/.yacba/strands/sessions/my-session/agents/agent/messages -v
```

**Output**:
```
=== SESSION STATISTICS ===

Total Messages:           166
User Messages (text):     9
Tool Results:             74
Assistant Messages:       34
Tool Uses:                49
Parse Errors:             0

Session Duration:         3545s (00:59:05)
First Message:            2025-11-28T14:08:11.496856+00:00
Last Message:             2025-11-28T15:07:16.176386+00:00
```

#### Diagnose Issues
```bash
./session-doctor.sh diagnose ~/.yacba/strands/sessions/my-session/agents/agent/messages
```

**Output**:
```
ERROR: [2] Tool result has no matching tool use (toolUseId: tooluse_xyz...)
ERROR: [45] Expected tool result after tool use, but got assistant text
WARNING: Found 2 issue(s) in session
```

#### Rollback User Messages
```bash
# Roll back last 2 user messages
./session-doctor.sh rollback ~/.yacba/strands/sessions/my-session/agents/agent/messages -n 2

# With auto-confirm (dangerous!)
./session-doctor.sh rollback ~/.yacba/strands/sessions/my-session/agents/agent/messages -n 1 -y
```

**Interactive output**:
```
Will delete 15 message file(s):
  - message_45.json: Please analyze the code...
  - message_46.json: Tool: file_read
  - message_47.json: Result: tooluse_abc...
  ...

Proceed with rollback? [y/N]
```

#### Fix Corruptions
```bash
./session-doctor.sh fix ~/.yacba/strands/sessions/my-session/agents/agent/messages

# Auto-confirm
./session-doctor.sh fix ~/.yacba/strands/sessions/my-session/agents/agent/messages -y
```

#### Create Backup
```bash
# Default backup location
./session-doctor.sh backup ~/.yacba/strands/sessions/my-session/agents/agent/messages

# Custom backup directory
./session-doctor.sh backup ~/.yacba/strands/sessions/my-session/agents/agent/messages \
  -b /path/to/backups
```

#### List Messages
```bash
./session-doctor.sh list ~/.yacba/strands/sessions/my-session/agents/agent/messages
```

**Output**:
```
IDX  ROLE       TYPE        PREVIEW
---  ---------  ----------  -------
0    user       text        in the ./code folder you will find...
1    assistant  text        I'll analyze the Rust workspace...
2    user       toolResult  Result: tooluse_ruIsEeHhScKo...
3    assistant  toolUse     Tool: file_read
```

#### Validate Structure
```bash
./session-doctor.sh validate ~/.yacba/strands/sessions/my-session/agents/agent/messages
```

## Message Structure Reference

The script expects messages in this format:

### User Text Message (actual user input)
```json
{
  "message": {
    "role": "user",
    "content": [{"text": "Your message here"}]
  },
  "message_id": 0,
  "created_at": "2025-11-28T14:08:11.496856+00:00",
  "updated_at": "2025-11-28T14:08:11.496862+00:00"
}
```

### Assistant Text Message (AI response)
```json
{
  "message": {
    "role": "assistant",
    "content": [{"text": "Response here"}]
  },
  "message_id": 1,
  ...
}
```

### Tool Use (AI invokes a tool)
```json
{
  "message": {
    "role": "assistant",
    "content": [{
      "toolUse": {
        "toolUseId": "tooluse_XYZ123...",
        "name": "file_read",
        "input": {...}
      }
    }]
  },
  "message_id": 3,
  ...
}
```

### Tool Result (system response)
```json
{
  "message": {
    "role": "user",
    "content": [{
      "toolResult": {
        "toolUseId": "tooluse_XYZ123...",
        "content": [...]
      }
    }]
  },
  "message_id": 4,
  ...
}
```

## Common Scenarios

### Scenario 1: Session Crashed During Tool Execution
**Problem**: Last message is a tool use, but no result exists. Session won't reload.

**Solution**:
```bash
# Diagnose to confirm
./session-doctor.sh diagnose ~/session/messages

# Fix automatically
./session-doctor.sh fix ~/session/messages
```

### Scenario 2: Want to Undo Last User Request
**Problem**: Asked the agent to do something problematic, want to remove it.

**Solution**:
```bash
# Roll back the last user message and everything after it
./session-doctor.sh rollback ~/session/messages -n 1
```

### Scenario 3: Session Has Tool Result Without Tool Use
**Problem**: Corruption where tool results exist but their tool uses are missing.

**Solution**:
```bash
# Diagnose shows orphaned tool results
./session-doctor.sh diagnose ~/session/messages

# Manual fix: identify the problematic message index
# Delete from that point onwards
rm ~/session/messages/message_{N..999}.json
```

### Scenario 4: Want to Analyze Session Before Sharing
**Problem**: Need to check what data is in the session.

**Solution**:
```bash
# Get overview
./session-doctor.sh stats ~/session/messages -v

# List all messages
./session-doctor.sh list ~/session/messages | less
```

## Options Reference

| Option | Description | Example |
|--------|-------------|---------|
| `-n, --number N` | Number of messages to roll back | `-n 3` |
| `-b, --backup-dir DIR` | Custom backup directory | `-b /backups` |
| `-y, --yes` | Skip confirmation prompts | `-y` |
| `-v, --verbose` | Verbose output | `-v` |
| `-h, --help` | Show help message | `-h` |

## Safety Features

1. **Automatic Backups**: `rollback` and `fix` always create backups first
2. **Confirmation Prompts**: Destructive operations require confirmation (unless `-y`)
3. **Preview**: Shows what will be deleted before deletion
4. **Non-Destructive Commands**: `stats`, `diagnose`, `list`, `validate` never modify files

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error or issues found |

## Limitations

1. **Read-only during diagnosis**: Diagnose doesn't modify files
2. **Fix is aggressive**: Removes from first problem onwards (safest approach)
3. **No undo for rollback**: Must restore from backup
4. **Assumes sequential files**: Expects `message_0.json`, `message_1.json`, etc.

## Advanced Usage

### Scripting
```bash
#!/bin/bash
# Automated session health check

SESSION_DIR="~/.yacba/strands/sessions/my-session/agents/agent/messages"

# Check health
if ! ./session-doctor.sh diagnose "$SESSION_DIR" > /dev/null 2>&1; then
  echo "Session has issues, attempting fix..."
  ./session-doctor.sh fix "$SESSION_DIR" -y
fi

# Always backup before starting work
./session-doctor.sh backup "$SESSION_DIR"
```

### Integration with CI/CD
```bash
# In test pipeline
./session-doctor.sh validate "$SESSION_DIR" || exit 1
```

### Multiple Sessions
```bash
# Check all sessions
for session in ~/.yacba/strands/sessions/*/agents/*/messages; do
  echo "Checking: $session"
  ./session-doctor.sh diagnose "$session"
  echo "---"
done
```

## Troubleshooting

### "Missing required dependencies"
Install `jq` and `bc`:
```bash
sudo apt-get install jq bc  # Ubuntu/Debian
brew install jq bc          # macOS
```

### "No message files found"
Check the directory path. Should contain `message_*.json` files.

### "Tool use/result mismatch"
This is normal if some tool uses have multiple content blocks. The warning appears when counts don't match, but this doesn't always indicate corruption.

### Backup restoration
```bash
# Manual restore
cp -r ./session-backups/my-session-20231128-150000/messages/* \
  ~/.yacba/strands/sessions/my-session/agents/agent/messages/
```

## Contributing

The script uses:
- **bash** for scripting logic
- **jq** for JSON parsing and manipulation
- **standard Unix tools** (find, sort, sed, bc, date)

To extend functionality, add new `cmd_*` functions and register in the `main()` case statement.

## License

This tool is provided as-is for session management and repair purposes.

## Version History

- **1.0.0**: Initial release
  - Statistics, diagnose, rollback, fix, backup, list, validate commands
  - Automatic backups for destructive operations
  - Color-coded output
  - Comprehensive error detection
