# Session Doctor - Quick Reference

## One-Liner Commands

```bash
# Set your session directory
SESSION="~/.yacba/strands/sessions/YOUR_SESSION/agents/agent_name/messages"

# Quick health check
./session-doctor.sh diagnose "$SESSION"

# Show statistics
./session-doctor.sh stats "$SESSION"

# Show statistics with tool breakdown
./session-doctor.sh stats "$SESSION" -v

# List all messages
./session-doctor.sh list "$SESSION"

# Validate JSON integrity
./session-doctor.sh validate "$SESSION"

# Create backup
./session-doctor.sh backup "$SESSION"

# Roll back last user message (with confirmation)
./session-doctor.sh rollback "$SESSION" -n 1

# Roll back last 3 user messages (auto-confirm, dangerous!)
./session-doctor.sh rollback "$SESSION" -n 3 -y

# Auto-fix corruption (with confirmation)
./session-doctor.sh fix "$SESSION"

# Auto-fix corruption (no confirmation)
./session-doctor.sh fix "$SESSION" -y
```

## Message Type Patterns

| Role | Content Type | What It Is | Example |
|------|--------------|------------|---------|
| `user` | `text` | **Real user input** | "Analyze this code..." |
| `user` | `toolResult` | Tool execution result | File contents, shell output |
| `assistant` | `text` | AI response to user | "I'll help you with..." |
| `assistant` | `toolUse` | AI calling a tool | `file_read`, `shell`, etc. |

## Understanding Diagnosis Output

### No Issues
```
SUCCESS: No issues found. Session is healthy.
```

### Orphaned Tool Use
```
ERROR: [45] Expected tool result after tool use, but got assistant text
```
**Meaning**: Message 45 called a tool, but message 46 is not the result.
**Fix**: `./session-doctor.sh fix` removes from message 45 onwards.

### Orphaned Tool Result
```
ERROR: [23] Tool result has no matching tool use (toolUseId: tooluse_abc...)
```
**Meaning**: Message 23 is a tool result, but the tool call doesn't exist.
**Cause**: Usually from incomplete message loading or corruption.
**Fix**: Manual deletion or `fix` command (if it's at the end).

### Tool Use/Result Mismatch
```
WARNING: Tool use/result mismatch: 49 uses vs 74 results
```
**Meaning**: Counts don't match. May be normal (some tools return multiple results in one message) or indicate corruption.
**Action**: Run `diagnose` for details.

## Common Workflows

### Workflow 1: Session Won't Load (Crashed Mid-Execution)
```bash
# 1. Diagnose
./session-doctor.sh diagnose "$SESSION"
# Shows: ERROR: [165] orphaned tool use

# 2. Fix automatically
./session-doctor.sh fix "$SESSION"
# Removes message 165 onwards, creates backup

# 3. Verify
./session-doctor.sh diagnose "$SESSION"
# Shows: SUCCESS: No issues found
```

### Workflow 2: Remove Last User Interaction
```bash
# 1. See what you have
./session-doctor.sh list "$SESSION" | tail -20

# 2. Roll back last user message
./session-doctor.sh rollback "$SESSION" -n 1
# Shows what will be deleted, asks for confirmation

# 3. Verify
./session-doctor.sh stats "$SESSION"
```

### Workflow 3: Regular Maintenance
```bash
# Create periodic backups
./session-doctor.sh backup "$SESSION" -b ~/session-backups

# Check health before important work
./session-doctor.sh diagnose "$SESSION" && echo "Ready to proceed"

# Get statistics after long sessions
./session-doctor.sh stats "$SESSION" -v
```

### Workflow 4: Debug Strange Behavior
```bash
# 1. Get overview
./session-doctor.sh stats "$SESSION" -v

# 2. List recent messages
./session-doctor.sh list "$SESSION" | tail -30

# 3. Check specific message
jq '.' "$SESSION/message_165.json"

# 4. Run full diagnosis
./session-doctor.sh diagnose "$SESSION"
```

## Emergency Recovery

### Scenario: Accidentally Deleted Messages
```bash
# Restore from most recent backup
ls -lt ./session-backups/  # Find most recent

# Copy back
cp -r ./session-backups/my-session-20231128-150000/messages/* "$SESSION/"
```

### Scenario: Session Completely Broken
```bash
# 1. Backup current state (even if broken)
./session-doctor.sh backup "$SESSION" -b ~/broken-session-backup

# 2. Try fix
./session-doctor.sh fix "$SESSION" -y

# 3. If still broken, manual recovery:
# Find last good message
./session-doctor.sh list "$SESSION"

# Delete from problem point onwards
cd "$SESSION"
rm message_{N..999}.json  # Replace N with problem index
```

### Scenario: Need to Restart from Specific Point
```bash
# 1. Backup first
./session-doctor.sh backup "$SESSION"

# 2. Find cutoff point
./session-doctor.sh list "$SESSION"

# 3. Delete from that point
cd "$SESSION"
rm message_{50..999}.json  # Keeps 0-49, deletes 50+

# 4. Verify
./session-doctor.sh diagnose "$SESSION"
```

## Understanding Message Sequences

### Valid Sequence
```
0: user (text) → "Please analyze..."
1: assistant (text) → "I'll analyze..."
2: assistant (toolUse) → file_read
3: user (toolResult) → [file contents]
4: assistant (text) → "Based on the file..."
```

### Invalid: Orphaned Tool Use
```
0: user (text) → "Please analyze..."
1: assistant (toolUse) → file_read
2: assistant (text) → "Based on the file..."  ← ERROR: Expected toolResult
```

### Invalid: Orphaned Tool Result
```
0: user (text) → "Please analyze..."
1: user (toolResult) → [file contents]  ← ERROR: No matching toolUse
```

## Statistics Interpretation

```
Total Messages:           166    ← All messages
User Messages (text):     9      ← Actual user inputs only
Tool Results:             74     ← Tool execution results
Assistant Messages:       34     ← AI text responses
Tool Uses:                49     ← AI tool calls
Parse Errors:             0      ← JSON parsing failures
```

**Healthy session**: Tool Uses ≈ Tool Results (some variance is OK)
**Problematic**: Parse Errors > 0, or large Tool Use/Result gap

## Tips

1. **Always backup before destructive operations** (rollback, fix)
2. **Use `-v` with stats** to see which tools are used most
3. **Run diagnose regularly** during long sessions
4. **Check the last few messages** if agent behaves strangely
5. **Keep backups** at key milestones in your work

## Shell Aliases (Optional)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Session doctor shortcuts
alias sd='/path/to/session-doctor.sh'
alias sd-stats='sd stats'
alias sd-check='sd diagnose'
alias sd-fix='sd fix'
alias sd-backup='sd backup'
alias sd-rollback='sd rollback'

# Quick check current session
function sd-quick() {
    local session="$1"
    echo "=== Statistics ===" && sd stats "$session"
    echo && echo "=== Diagnosis ===" && sd diagnose "$session"
}
```

Usage:
```bash
sd-quick ~/.yacba/strands/sessions/my-session/agents/agent/messages
```

## File Locations

- **Script**: `./session-doctor.sh`
- **Backups**: `./session-backups/` (default)
- **Session messages**: `~/.yacba/strands/sessions/SESSION_NAME/agents/AGENT_NAME/messages/`

## Getting Help

```bash
# Show help
./session-doctor.sh --help

# Check version
head -n 10 ./session-doctor.sh | grep VERSION
```
