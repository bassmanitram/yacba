# Session Doctor

A bash/jq tool for analyzing, diagnosing, and repairing AI agent session message sequences.

## Quick Start

```bash
# Make executable
chmod +x session-doctor.sh

# Check health
./session-doctor.sh diagnose yacba-3

# View statistics
./session-doctor.sh stats yacba-3 -v
```

### Dependencies
```bash
# Ubuntu/Debian
sudo apt-get install jq bc

# macOS  
brew install jq bc
```

## Commands

| Command | Description | Modifies Files |
|---------|-------------|----------------|
| `stats` | Show session metrics and tool usage | No |
| `diagnose` | Detect corruption and integrity issues | No |
| `list` | View all messages with previews | No |
| `validate` | Check JSON and structure validity | No |
| `backup` | Create timestamped backup | No |
| `rollback` | Remove N user messages and their responses | **Yes** |
| `fix` | Auto-repair orphaned tool calls | **Yes** |

## Usage

```bash
./session-doctor.sh <command> <session_name> [agent_name] [options]
```

### Arguments
- **session_name**: Session name like `yacba-3` (required)
- **agent_name**: Specific agent name (optional, auto-detects first if omitted)

### Options
- `-s, --session-base <DIR>` - Session base directory (default: `~/.yacba/strands/sessions`)
- `-n, --number <N>` - Number of messages to roll back
- `-b, --backup-dir <DIR>` - Backup directory (default: `./session-backups`)
- `-y, --yes` - Skip confirmation prompts
- `-v, --verbose` - Verbose output with tool breakdown
- `-h, --help` - Show help

## Examples

```bash
# Diagnose session health
./session-doctor.sh diagnose yacba-3

# Get statistics with tool breakdown
./session-doctor.sh stats yacba-3 -v

# List recent messages
./session-doctor.sh list yacba-3 | tail -20

# Create backup before making changes
./session-doctor.sh backup yacba-3

# Roll back last user message (with confirmation)
./session-doctor.sh rollback yacba-3 -n 1

# Auto-fix orphaned tool calls
./session-doctor.sh fix yacba-3

# Specify agent and custom session base
./session-doctor.sh stats yacba-3 my_agent -s /custom/sessions
```

## Common Workflows

### Session Crashed Mid-Execution
```bash
./session-doctor.sh diagnose yacba-3  # Identify issue
./session-doctor.sh fix yacba-3       # Remove orphaned tool calls
./session-doctor.sh diagnose yacba-3  # Verify fix
```

### Undo Last User Request
```bash
./session-doctor.sh list yacba-3 | tail -20  # Review recent messages
./session-doctor.sh rollback yacba-3 -n 1    # Remove last interaction
```

### Regular Maintenance
```bash
./session-doctor.sh backup yacba-3           # Backup before work
./session-doctor.sh diagnose yacba-3         # Check health
./session-doctor.sh stats yacba-3 -v         # Review activity
```

### Multiple Agents
```bash
./session-doctor.sh stats yacba-3 agent_primary -v
./session-doctor.sh stats yacba-3 agent_backup -v
```

### Custom Session Storage
```bash
./session-doctor.sh diagnose yacba-3 -s /mnt/data/sessions
```

## Understanding Output

### Statistics
```
=== TARGET AGENT SESSION ===
/home/user/.yacba/strands/sessions/session_yacba-3/agents/agent_strands/messages

=== SESSION STATISTICS ===
Total Messages:                166
  User Messages (text):        9      # Actual user inputs
  Tool Results:                74     # Tool execution results
  Assistant Messages (text):   34     # AI text responses
  Tool Uses:                   74     # AI tool calls
  Multi-block Messages:        25     # Messages with multiple content blocks

Session Duration:              3545s (00:59:05)

✓ Tool uses and results balanced (74 = 74)
```

### Diagnosis Errors

**Orphaned Tool Use** - Tool called but no result exists:
```
ERROR: [45] Orphaned tool use: tooluse_abc... (no matching result)
```
**Fix**: Run `./session-doctor.sh fix yacba-3`

**Orphaned Tool Result** - Result exists but no matching call:
```
ERROR: [23] Tool result has no matching tool use (toolUseId: tooluse_xyz...)
```
**Fix**: Typically requires manual cleanup after backup

**Tool Use/Result Mismatch** - Counts don't match:
```
WARNING: Tool use/result mismatch: 49 uses vs 74 results
```
**Note**: May be normal if tools return multiple results per call

## Message Flow Examples

### Healthy Sequence
```
0: user (text)       → "Please analyze the code"
1: assistant (text)  → "I'll analyze it"
2: assistant (toolUse) → file_read
3: user (toolResult) → [file contents]
4: assistant (text)  → "Here's my analysis..."
```

### Orphaned Tool Use (Error)
```
0: user (text)       → "Read file"
1: assistant (toolUse) → file_read
2: assistant (text)  → "Based on the file..."  ← ERROR: Expected toolResult
```

## Session Path Resolution

The script resolves session names automatically:

```
Input:        yacba-3
Base:         ~/.yacba/strands/sessions (default)
Full path:    ~/.yacba/strands/sessions/session_yacba-3/agents/<agent>/messages
Agent:        [first agent alphabetically or specified]
```

Override with `-s`:
```bash
./session-doctor.sh stats yacba-3 -s /custom/path
# Resolves to: /custom/path/session_yacba-3/agents/<agent>/messages
```

## Safety Features

- **Read-only by default**: Most commands don't modify files
- **Automatic backups**: `rollback` and `fix` create backups before changes
- **Confirmation prompts**: Destructive operations require explicit confirmation
- **Preview changes**: Shows what will be deleted before doing it
- **Path transparency**: Always displays which session is being operated on

## Rollback Behavior

Rollback removes the target user message AND everything that follows:

```
BEFORE rollback -n 1:
  message_0-4: [earlier conversation]
  message_5: user "Do Y"        ← Target
  message_6-9: [Y conversation] ← All deleted

AFTER:
  message_0-4: [earlier conversation]
  [session ends here]
```

## Fix Behavior

Fix removes from the first orphaned tool call onwards:

```
BEFORE:
  message_0-45: [healthy messages]
  message_46: assistant toolUse ← ORPHANED
  message_47-52: [subsequent messages]

AFTER fix:
  message_0-45: [healthy messages]
  [messages 46-52 deleted]
```

## Advanced Usage

### Scripting
```bash
#!/bin/bash
SESSION="yacba-3"

# Health check and auto-fix
if ! ./session-doctor.sh diagnose "$SESSION" &>/dev/null; then
  echo "Issues found, fixing..."
  ./session-doctor.sh fix "$SESSION" -y
fi

# Backup before starting work
./session-doctor.sh backup "$SESSION"
```

### Check All Agents
```bash
#!/bin/bash
SESSION="yacba-3"
BASE="$HOME/.yacba/strands/sessions"
AGENTS_DIR="$BASE/session_${SESSION}/agents"

for agent_dir in "$AGENTS_DIR"/*; do
  agent=$(basename "$agent_dir")
  echo "=== $agent ==="
  ./session-doctor.sh diagnose "$SESSION" "$agent"
done
```

### Shell Aliases
```bash
# Add to ~/.bashrc or ~/.zshrc
alias sd='./session-doctor.sh'
alias sd-check='sd diagnose'
alias sd-fix='sd fix'
alias sd-stats='sd stats'

# Quick health check
function sd-quick() {
    sd stats "$1" && sd diagnose "$1"
}
```

## Troubleshooting

### "Missing required dependencies"
Install jq and bc:
```bash
sudo apt-get install jq bc  # Ubuntu/Debian
brew install jq bc          # macOS
```

### "Session directory does not exist"
Check session name and base path. Sessions must be named `session_<name>`.

### "No agent directories found"
Verify agents exist:
```bash
ls ~/.yacba/strands/sessions/session_yacba-3/agents/
```

### "No message files found"
Directory exists but contains no `message_*.json` files.

### Restore from Backup
```bash
# Find backup
ls -lt ./session-backups/

# Restore
cp -r ./session-backups/session_yacba-3-20231128-150000/* \
  ~/.yacba/strands/sessions/session_yacba-3/agents/agent_name/messages/
```

## Message Structure

**User messages** contain:
- `text` - User input
- `toolResult` - Tool execution results

**Assistant messages** contain:
- `text` - Explanations and responses
- `toolUse` - Tool invocations

**Multi-block messages** (normal):
```json
{
  "message": {
    "role": "assistant",
    "content": [
      {"text": "I'll read that file"},
      {"toolUse": {"name": "file_read", ...}}
    ]
  }
}
```

## Exit Codes

- `0` - Success, no issues found
- `1` - Errors found or operation failed

## Limitations

- Diagnosis doesn't modify files
- Fix removes from first problem onwards (conservative approach)
- No undo for rollback (must restore from backup)
- Assumes sequential message numbering (`message_0.json`, `message_1.json`, etc.)
- Assumes session naming convention: `session_<name>`

## License

Provided as-is for session management and repair.
