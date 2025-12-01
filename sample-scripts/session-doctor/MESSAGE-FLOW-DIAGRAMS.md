# Message Flow Diagrams

Visual representations of message sequences and how Session Doctor interprets them.

## Healthy Message Sequences

### Basic User-Assistant Exchange
```
┌─────────────────────────────────────────────────────────┐
│ message_0.json                                          │
│ role: user                                              │
│ content: [{text: "Please help me with X"}]             │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ message_1.json                                          │
│ role: assistant                                         │
│ content: [{text: "I'll help you with X"}]              │
└─────────────────────────────────────────────────────────┘
```

### Tool Use Sequence (Healthy)
```
┌─────────────────────────────────────────────────────────┐
│ message_0.json                                          │
│ role: user                                              │
│ content: [{text: "Show me file.txt"}]                  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ message_1.json                                          │
│ role: assistant                                         │
│ content: [{text: "I'll read that file for you"}]       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ message_2.json                                          │
│ role: assistant                                         │
│ content: [{toolUse: {                                   │
│   toolUseId: "ABC123",                                  │
│   name: "file_read",                                    │
│   input: {path: "file.txt"}                             │
│ }}]                                                     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ message_3.json                                          │
│ role: user                                              │
│ content: [{toolResult: {                                │
│   toolUseId: "ABC123",  ← MATCHES!                     │
│   content: "File contents here..."                      │
│ }}]                                                     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ message_4.json                                          │
│ role: assistant                                         │
│ content: [{text: "Here's the file content..."}]        │
└─────────────────────────────────────────────────────────┘
```

### Multiple Tool Calls in Sequence
```
User: "List files and read config"
  ↓
Assistant: "I'll do that"
  ↓
Assistant: toolUse(shell, "ls")  [toolUseId: A]
  ↓
User: toolResult [toolUseId: A] → output
  ↓
Assistant: toolUse(file_read, "config") [toolUseId: B]
  ↓
User: toolResult [toolUseId: B] → contents
  ↓
Assistant: "Here's what I found..."
```

## Corrupted Sequences (What Session Doctor Detects)

### ERROR 1: Orphaned Tool Use
```
┌─────────────────────────────────────────────────────────┐
│ message_10.json                                         │
│ role: assistant                                         │
│ content: [{toolUse: {                                   │
│   toolUseId: "XYZ789",                                  │
│   name: "shell"                                         │
│ }}]                                                     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ message_11.json                                         │
│ role: assistant                  ← ERROR!               │
│ content: [{text: "..."}]        ← Expected toolResult!  │
└─────────────────────────────────────────────────────────┘

Session Doctor Output:
  ERROR: [11] Expected tool result after tool use, 
              but got assistant text
  Previous tool use: message_10.json (toolUseId: XYZ789)
```

### ERROR 2: Orphaned Tool Result
```
┌─────────────────────────────────────────────────────────┐
│ message_20.json                                         │
│ role: assistant                                         │
│ content: [{text: "Some response"}]                     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ message_21.json                                         │
│ role: user                      ← ERROR!                │
│ content: [{toolResult: {        ← No matching toolUse!  │
│   toolUseId: "MISSING",                                 │
│   content: "..."                                        │
│ }}]                                                     │
└─────────────────────────────────────────────────────────┘

Session Doctor Output:
  ERROR: [21] Tool result has no matching tool use
              (toolUseId: MISSING)
```

### ERROR 3: Session Crash Mid-Execution
```
User: "Please analyze file"
  ↓
Assistant: "I'll read it"
  ↓
Assistant: toolUse(file_read) [toolUseId: CRASH]
  ↓
[SESSION CRASHED - No tool result written]
  ↓
[Session won't reload - expects tool result]

Session Doctor Fix:
  Removes message with toolUse(CRASH) and everything after
  Session can now reload
```

### ERROR 4: Missing Message IDs
```
message_0.json  ✓
message_1.json  ✓
message_2.json  ✓
message_4.json  ← Gap! (message_3.json missing)
message_5.json

Session Doctor Output:
  WARNING: Possible gap in sequence
           (Message 3 not found)
```

## Rollback Behavior

### Rolling Back 1 User Message
```
BEFORE:
  message_0: user "Do X"
  message_1: assistant "OK"
  message_2: assistant toolUse
  message_3: user toolResult
  message_4: assistant "Done X"
  message_5: user "Do Y"        ← Target for rollback
  message_6: assistant "OK"
  message_7: assistant toolUse
  message_8: user toolResult
  message_9: assistant "Done Y"

AFTER ROLLBACK -n 1:
  message_0: user "Do X"
  message_1: assistant "OK"
  message_2: assistant toolUse
  message_3: user toolResult
  message_4: assistant "Done X"
  [messages 5-9 deleted]

Result: Removed "Do Y" request and all its consequences
```

### Rolling Back 2 User Messages
```
BEFORE:
  message_0: user "Do X"
  message_1-4: [X conversation]
  message_5: user "Do Y"
  message_6-9: [Y conversation]
  message_10: user "Do Z"       ← Will be deleted
  message_11-14: [Z conversation]

AFTER ROLLBACK -n 2:
  message_0: user "Do X"
  message_1-4: [X conversation]
  [messages 5-14 deleted]

Result: Kept only "Do X" conversation
```

## Fix Command Behavior

### Scenario: Orphaned Tool Use at End
```
BEFORE:
  message_0-97: [healthy messages]
  message_98: assistant toolUse ← ORPHANED (no result)
  message_99: assistant text     ← Invalid sequence

DIAGNOSIS:
  ERROR: [99] Expected tool result after tool use

FIX:
  Removes message_98 and message_99
  
AFTER:
  message_0-97: [healthy messages]
  [Session now healthy]
```

### Scenario: Multiple Orphaned Tool Uses
```
BEFORE:
  message_0-45: [healthy]
  message_46: assistant toolUse ← ORPHANED
  message_47: assistant text
  message_48-50: [various messages]
  message_51: assistant toolUse ← ORPHANED
  message_52: assistant text

FIX STRATEGY:
  Finds earliest orphaned (message_46)
  Removes from 46 onwards
  
AFTER:
  message_0-45: [healthy]
  [messages 46-52 deleted]
```

## Statistics Interpretation

### Healthy Balance
```
Total Messages:    100
User (text):       10  ──┐
Tool Results:      40    │  User role total: 50
                      ──┘
Assistant (text):  20  ──┐
Tool Uses:         40    │  Assistant role total: 50
                      ──┘

Tool balance: 40 uses = 40 results ✓
```

### Imbalanced (May Indicate Issue)
```
Total Messages:    100
User (text):       10
Tool Results:      45  ← More results than uses?
Assistant (text):  20
Tool Uses:         25  ← Fewer uses?

WARNING: Tool use/result mismatch: 25 uses vs 45 results

Possible causes:
- Some tools return multiple results in one message
- Missing tool use messages (corruption)
- Tool result without matching tool use
```

## Message Type Distribution (Real Example)

From your session analysis:
```
Total: 166 messages
┌────────────────────────────────────────────────┐
│ User (text):      9  (5.4%)   [User input]    │
│ Tool Results:     74 (44.6%)  [System]        │
│ Assistant (text): 34 (20.5%)  [AI response]   │
│ Tool Uses:        49 (29.5%)  [AI tool calls] │
└────────────────────────────────────────────────┘

Interpretation:
- 9 user prompts generated 166 messages
- Average 18.4 messages per user input
- Heavy tool usage (74 results from 49 uses)
- 25 orphaned tool results detected
```

## Tool Call Patterns

### Pattern 1: Single Tool Call
```
User: "Read file"
  → Assistant: toolUse(file_read)
  → User: toolResult
  → Assistant: "Here's the content"
```

### Pattern 2: Sequential Tool Calls
```
User: "Build and test"
  → Assistant: toolUse(shell, "cargo build")
  → User: toolResult
  → Assistant: toolUse(shell, "cargo test")
  → User: toolResult
  → Assistant: "Build and tests passed"
```

### Pattern 3: Exploratory Pattern
```
User: "Analyze the codebase"
  → Assistant: toolUse(file_read, "Cargo.toml")
  → User: toolResult
  → Assistant: toolUse(shell, "find src")
  → User: toolResult
  → Assistant: toolUse(file_read, "src/main.rs")
  → User: toolResult
  → Assistant: toolUse(file_read, "src/lib.rs")
  → User: toolResult
  → Assistant: "Here's my analysis..."
```

## Backup and Restore Flow

### Backup Process
```
Original Session:
  ~/.yacba/sessions/my-session/agents/agent/messages/
    ├── message_0.json
    ├── message_1.json
    └── ...

Run Backup:
  $ ./session-doctor.sh backup <session-dir>

Result:
  ./session-backups/my-session-20231128-150000/
    └── messages/
        ├── message_0.json
        ├── message_1.json
        └── ...

Both directories now exist (original untouched)
```

### Restore Process
```
Corrupted Session:
  ~/.yacba/sessions/my-session/agents/agent/messages/
    ├── message_0.json
    ├── message_1.json (corrupted)
    └── message_2.json

Backup Available:
  ./session-backups/my-session-20231128-150000/messages/

Manual Restore:
  $ cp -r ./session-backups/.../messages/* \
      ~/.yacba/sessions/my-session/agents/agent/messages/

Restored Session:
  All files copied back from backup
```

## Command Decision Tree

```
                    Start Here
                        |
        Do you need to modify the session?
                    /       \
                  NO         YES
                  |           |
         ┌────────┴────────┐  |
         |                 |  |
    Want stats?    Want to view?  
         |                 |  |
      [stats]          [list]  |
         |                 |  |
    Want diagnosis?   Want validation?
         |                 |
     [diagnose]       [validate]
                           |
                    ┌──────┴──────┐
                    |             |
            Need to remove?   Need to fix?
                    |             |
            [rollback -n N]   [fix]
                    |             |
            Creates backup  Creates backup
```

## Visual Legend

```
┌─────────────────────────────────────┐
│ Message File                        │  Single message
└─────────────────────────────────────┘

        ↓                                 Flow direction

✓                                         Healthy/OK
✗ or ERROR!                               Problem detected
← or →                                    Emphasis/note

[command]                                 Session Doctor command
```

## Real-World Example Timeline

Your session (simplified):
```
14:08:11  msg_0   user: "Analyze Rust workspace"
14:08:20  msg_1   asst: "I'll analyze..."
14:08:20  msg_2   user: toolResult (shell ls)
14:08:22  msg_3   asst: toolUse(file_read Cargo.toml)
14:08:23  msg_4   user: toolResult
14:08:25  msg_5   asst: toolUse(shell cargo metadata)
14:08:26  msg_6   user: toolResult
    ...   [multiple tool executions]
15:07:16  msg_165 asst: "Final analysis complete"

Duration: 59 minutes
Activity: 166 messages (2.8 messages/minute)
Tool calls: 49 total (0.83 calls/minute)
```

This shows intense automated tool usage driven by a single complex user request.
