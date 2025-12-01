# Session Doctor

A professional bash/jq tool for analyzing, diagnosing, and repairing AI agent session message sequences.

## Quick Start

### Installation
```bash
chmod +x session-doctor.sh

# Test it
./session-doctor.sh stats ~/.yacba/strands/sessions/YOUR_SESSION/agents/AGENT/messages
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
| `stats` | Show session metrics | No |
| `diagnose` | Detect corruption | No |
| `list` | View all messages | No |
| `validate` | Check JSON integrity | No |
| `backup` | Create timestamped backup | No |
| `rollback` | Remove N user messages | **Yes** |
| `fix` | Auto-repair corruptions | **Yes** |

## Example Usage

```bash
SESSION="~/.yacba/strands/sessions/YOUR_SESSION/agents/AGENT/messages"

# Check health
./session-doctor.sh diagnose "$SESSION"

# View statistics with tool breakdown
./session-doctor.sh stats "$SESSION" -v

# List all messages
./session-doctor.sh list "$SESSION"

# Create backup (always do this first!)
./session-doctor.sh backup "$SESSION"

# Roll back last user message
./session-doctor.sh rollback "$SESSION" -n 1

# Auto-fix corruption
./session-doctor.sh fix "$SESSION"
```

## Real-World Example Output

From an actual session analysis:

```
=== SESSION STATISTICS ===

Total Messages:                166
  User Messages (text):        9
  Tool Results:                74
  Assistant Messages (text):   34
  Tool Uses:                   74
  Multi-block Messages:        25
  Parse Errors:                0

Session Duration:              3545s (00:59:05)

✓ Tool uses and results balanced (74 = 74)

=== TOOL USAGE BREAKDOWN ===
     56 shell
      9 file_write
      9 file_read

=== MULTI-BLOCK MESSAGES ===
Found 25 message(s) with multiple content blocks
(This is normal - assistant can send text + tool use together)
```

## Documentation

| File | Purpose |
|------|---------|
| [README.md](README.md) | This file - quick start |
| [SESSION-DOCTOR-README.md](SESSION-DOCTOR-README.md) | Comprehensive documentation |
| [QUICK-REFERENCE.md](QUICK-REFERENCE.md) | Command cheat sheet |
| [MESSAGE-FLOW-DIAGRAMS.md](MESSAGE-FLOW-DIAGRAMS.md) | Visual diagrams |

## Common Use Cases

### Session Crashed During Tool Execution
```bash
./session-doctor.sh diagnose "$SESSION"  # Confirm issue
./session-doctor.sh fix "$SESSION"       # Auto-repair
```

### Undo Last User Request  
```bash
./session-doctor.sh rollback "$SESSION" -n 1
```

### Regular Maintenance
```bash
# Before important work
./session-doctor.sh backup "$SESSION"

# Weekly health check
./session-doctor.sh diagnose "$SESSION"
```

## Message Structure

Session Doctor understands these content types:

**User messages** can contain:
- `text` - user input
- `image` - uploaded images
- `document` - attached documents  
- `toolResult` - system-generated tool execution results

**Assistant messages** can contain:
- `text` - explanations and responses
- `toolUse` - tool invocations

**Multi-block messages** (normal and healthy):
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

## Key Features

✅ Handles multi-block content correctly  
✅ Accurate tool use/result counting  
✅ Detects 7+ types of corruption  
✅ Automatic backups before destructive operations  
✅ Confirmation prompts for safety  
✅ Color-coded output  
✅ Zero external dependencies (except jq/bc)  

## Safety

- **Read-only by default**: Most commands don't modify files
- **Automatic backups**: `rollback` and `fix` create backups first
- **Confirmation prompts**: Destructive operations ask for confirmation
- **Preview changes**: Shows what will be modified before doing it

## License

Provided as-is for session management and repair.

## Getting Help

```bash
# Built-in help
./session-doctor.sh --help

# Full documentation
cat SESSION-DOCTOR-README.md | less

# Quick reference
cat QUICK-REFERENCE.md
```
