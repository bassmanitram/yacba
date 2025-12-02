#!/usr/bin/env bash

set -euo pipefail

# Session Doctor - AI Agent Session Analysis and Repair Tool
VERSION="1.1.0"
SCRIPT_NAME="$(basename "$0")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default session base directory
DEFAULT_SESSION_BASE="$HOME/.yacba/strands/sessions"

# Utility functions
error() {
    echo -e "${RED}ERROR: $*${NC}" >&2
}

warn() {
    echo -e "${YELLOW}WARNING: $*${NC}" >&2
}

info() {
    echo -e "${BLUE}INFO: $*${NC}" >&2
}

success() {
    echo -e "${GREEN}SUCCESS: $*${NC}" >&2
}

usage() {
    cat <<EOF
$SCRIPT_NAME v$VERSION - AI Agent Session Doctor

USAGE:
    $SCRIPT_NAME <command> <session_name> [agent_name] [options]

ARGUMENTS:
    session_name    Session name (e.g., 'yacba-3')
                    Will look in: <session_base>/session_<session_name>/agents/<agent>/messages
    
    agent_name      Optional: Specific agent name
                    If omitted, uses first agent found in alphabetical order

COMMANDS:
    stats       Show session statistics
    diagnose    Check for errors and corruptions in message sequence
    rollback    Roll back N user messages (interactive prompts only)
    fix         Attempt to fix corrupt tool use/result sequences
    backup      Create a backup of the session
    list        List all messages with summary
    validate    Validate JSON and structure integrity
    
OPTIONS:
    -s, --session-base <DIR>  Session base directory (default: ~/.yacba/strands/sessions)
    -n, --number <N>          Number of messages to roll back (for rollback command)
    -b, --backup-dir <DIR>    Directory for backups (default: ./session-backups)
    -y, --yes                 Skip confirmation prompts
    -v, --verbose             Verbose output
    -h, --help                Show this help message

EXAMPLES:
    # Use default session base, auto-detect first agent
    $SCRIPT_NAME stats yacba-3
    
    # Specify specific agent
    $SCRIPT_NAME diagnose yacba-3 my_agent
    
    # Use custom session base
    $SCRIPT_NAME stats yacba-3 -s /custom/sessions
    
    # All options together
    $SCRIPT_NAME rollback yacba-3 my_agent -s /custom/sessions -n 2

EOF
}

# Check dependencies
check_dependencies() {
    local missing=()
    for cmd in jq bc; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        error "Missing required dependencies: ${missing[*]}"
        error "Install with: sudo apt-get install ${missing[*]}"
        exit 1
    fi
}

# Resolve session name to full messages directory path
resolve_session_path() {
    local session_name="$1"
    local agent_name="${2:-}"
    local session_base="${3:-$DEFAULT_SESSION_BASE}"
    
    # Expand tilde in session_base
    session_base="${session_base/#\~/$HOME}"
    
    # Construct session directory path
    local session_dir="$session_base/session_${session_name}"
    
    if [ ! -d "$session_dir" ]; then
        error "Session directory does not exist: $session_dir"
        exit 1
    fi
    
    local agents_dir="$session_dir/agents"
    
    if [ ! -d "$agents_dir" ]; then
        error "Agents directory does not exist: $agents_dir"
        exit 1
    fi
    
    # If agent name not specified, find first agent
    if [ -z "$agent_name" ]; then
        agent_name=$(find "$agents_dir" -mindepth 1 -maxdepth 1 -type d -printf "%f\n" 2>/dev/null | sort | head -n 1)
        
        if [ -z "$agent_name" ]; then
            error "No agent directories found in: $agents_dir"
            exit 1
        fi
        
        info "Auto-detected agent: $agent_name"
    fi
    
    local messages_dir="$agents_dir/$agent_name/messages"
    
    if [ ! -d "$messages_dir" ]; then
        error "Messages directory does not exist: $messages_dir"
        exit 1
    fi
    
    echo "$messages_dir"
}

# Display the target session information
display_session_target() {
    local dir="$1"
    echo
    echo -e "${CYAN}=== TARGET AGENT SESSION ===${NC}"
    echo -e "${GREEN}$dir${NC}"
    echo
}

# Validate session directory
validate_session_dir() {
    local dir="$1"
    
    if [ ! -d "$dir" ]; then
        error "Directory does not exist: $dir"
        exit 1
    fi
    
    local count
    count=$(find "$dir" -maxdepth 1 -name "message_*.json" 2>/dev/null | wc -l)
    
    if [ "$count" -eq 0 ]; then
        error "No message files found in: $dir"
        exit 1
    fi
}

# Get sorted list of message files
get_message_files() {
    local dir="$1"
    find "$dir" -maxdepth 1 -name "message_*.json" -print0 | 
        xargs -0 -n1 basename | 
        sort -t_ -k2 -n | 
        sed "s|^|$dir/|"
}

# Extract message index from filename
get_message_index() {
    local file="$1"
    basename "$file" | sed 's/message_\([0-9]*\)\.json/\1/'
}

# Check if message has a specific content type (checks ALL content blocks)
message_has_content_type() {
    local file="$1"
    local type="$2"  # text, toolUse, toolResult
    
    jq -e ".message.content[] | select(has(\"$type\"))" "$file" > /dev/null 2>&1
}

# Get all tool use IDs from a message
get_tool_use_ids() {
    local file="$1"
    jq -r '.message.content[] | select(has("toolUse")) | .toolUse.toolUseId' "$file" 2>/dev/null || true
}

# Get all tool result IDs from a message
get_tool_result_ids() {
    local file="$1"
    jq -r '.message.content[] | select(has("toolResult")) | .toolResult.toolUseId' "$file" 2>/dev/null || true
}

# Get message classification (primary type for display)
get_message_type() {
    local file="$1"
    local role
    role=$(jq -r '.message.role' "$file" 2>/dev/null || echo "error")
    
    # Check what content blocks exist
    local has_text=false
    local has_tool_use=false
    local has_tool_result=false
    
    if message_has_content_type "$file" "text"; then
        has_text=true
    fi
    if message_has_content_type "$file" "toolUse"; then
        has_tool_use=true
    fi
    if message_has_content_type "$file" "toolResult"; then
        has_tool_result=true
    fi
    
    # Classify message
    if [ "$role" = "user" ]; then
        if [ "$has_text" = "true" ]; then
            echo "user_text"
        elif [ "$has_tool_result" = "true" ]; then
            echo "tool_result"
        fi
    elif [ "$role" = "assistant" ]; then
        if [ "$has_tool_use" = "true" ]; then
            echo "tool_use"  # May also have text
        elif [ "$has_text" = "true" ]; then
            echo "assistant_text"
        fi
    else
        echo "unknown"
    fi
}

# Get text preview from message
get_message_preview() {
    local file="$1"
    local preview=""
    
    # Get first text content
    preview=$(jq -r '.message.content[] | select(has("text")) | .text' "$file" 2>/dev/null | head -n 1 | head -c 60 | tr '\n' ' ' || true)
    if [ -z "$preview" ]; then
        # Or first tool name
        preview=$(jq -r '.message.content[] | select(has("toolUse")) | .toolUse.name' "$file" 2>/dev/null | head -n 1 || true)
        if [ -n "$preview" ]; then
            preview="Tool: $preview"
        fi
    fi
    
    echo "$preview"
}

# Statistics command
cmd_stats() {
    local dir="$1"
    local verbose="${2:-false}"
    
    display_session_target "$dir"
    
    info "Analyzing session..."
    echo
    
    local total=0
    local user_text=0
    local tool_results=0
    local assistant_text=0
    local tool_uses=0
    local multi_block=0
    local errors=0
    
    local first_msg=""
    local last_msg=""
    local first_time=""
    local last_time=""
    
    while IFS= read -r file; do
        total=$((total + 1))
        
        if [ -z "$first_msg" ]; then
            first_msg="$file"
            first_time=$(jq -r '.created_at' "$file")
        fi
        last_msg="$file"
        last_time=$(jq -r '.created_at' "$file")
        
        local role
        role=$(jq -r '.message.role' "$file" 2>/dev/null || echo "error")
        
        if [ "$role" = "error" ]; then
            errors=$((errors + 1))
            continue
        fi
        
        # Count content blocks
        local block_count
        block_count=$(jq '.message.content | length' "$file" 2>/dev/null || echo "0")
        if [ "$block_count" -gt 1 ]; then
            multi_block=$((multi_block + 1))
        fi
        
        # Count by content type (check ALL blocks)
        if [ "$role" = "user" ]; then
            if message_has_content_type "$file" "text"; then
                user_text=$((user_text + 1))
            fi
            if message_has_content_type "$file" "toolResult"; then
                # Count all tool results in this message
                local result_count
                result_count=$(jq '[.message.content[] | select(has("toolResult"))] | length' "$file")
                tool_results=$((tool_results + result_count))
            fi
        elif [ "$role" = "assistant" ]; then
            if message_has_content_type "$file" "text"; then
                assistant_text=$((assistant_text + 1))
            fi
            if message_has_content_type "$file" "toolUse"; then
                # Count all tool uses in this message
                local use_count
                use_count=$(jq '[.message.content[] | select(has("toolUse"))] | length' "$file")
                tool_uses=$((tool_uses + use_count))
            fi
        fi
    done < <(get_message_files "$dir")
    
    # Calculate session duration
    local duration="N/A"
    if [ -n "$first_time" ] && [ -n "$last_time" ]; then
        local start_epoch
        local end_epoch
        start_epoch=$(date -d "$first_time" +%s 2>/dev/null || echo "0")
        end_epoch=$(date -d "$last_time" +%s 2>/dev/null || echo "0")
        if [ "$start_epoch" != "0" ] && [ "$end_epoch" != "0" ]; then
            local diff=$((end_epoch - start_epoch))
            duration="${diff}s ($(date -u -d @${diff} +%H:%M:%S 2>/dev/null || echo "$diff seconds"))"
        fi
    fi
    
    # Display statistics
    echo -e "${CYAN}=== SESSION STATISTICS ===${NC}"
    echo
    echo "Total Messages:                $total"
    echo "  User Messages (text):        $user_text"
    echo "  Tool Results:                $tool_results"
    echo "  Assistant Messages (text):   $assistant_text"
    echo "  Tool Uses:                   $tool_uses"
    echo "  Multi-block Messages:        $multi_block"
    echo "  Parse Errors:                $errors"
    echo
    echo "Session Duration:              $duration"
    echo "First Message:                 $first_time"
    echo "Last Message:                  $last_time"
    echo
    
    # Tool balance check
    if [ $tool_uses -ne $tool_results ]; then
        warn "Tool use/result mismatch: $tool_uses uses vs $tool_results results"
    else
        success "Tool uses and results balanced ($tool_uses = $tool_results)"
    fi
    
    if [ "$verbose" = "true" ]; then
        echo
        echo -e "${CYAN}=== TOOL USAGE BREAKDOWN ===${NC}"
        
        while IFS= read -r file; do
            jq -r '.message.content[] | select(has("toolUse")) | .toolUse.name' "$file" 2>/dev/null || true
        done < <(get_message_files "$dir") | sort | uniq -c | sort -rn
        
        if [ "$multi_block" -gt 0 ]; then
            echo
            echo -e "${CYAN}=== MULTI-BLOCK MESSAGES ===${NC}"
            echo "Found $multi_block message(s) with multiple content blocks"
            echo "(This is normal - assistant can send text + tool use together)"
        fi
    fi
}

# Diagnose command
cmd_diagnose() {
    local dir="$1"
    
    display_session_target "$dir"
    
    info "Diagnosing session..."
    echo
    
    local issues=0
    
    # Build a complete map of all tool use IDs to their message index
    declare -A tool_use_map
    declare -A tool_result_map
    
    while IFS= read -r file; do
        local idx
        idx=$(get_message_index "$file")
        
        # Check JSON validity
        if ! jq empty "$file" 2>/dev/null; then
            error "[$idx] Invalid JSON in file: $file"
            issues=$((issues + 1))
            continue
        fi
        
        # Check required fields
        local role
        role=$(jq -r '.message.role // "missing"' "$file")
        if [ "$role" = "missing" ]; then
            error "[$idx] Missing 'message.role' field"
            issues=$((issues + 1))
            continue
        fi
        
        local message_id
        message_id=$(jq -r '.message_id // "missing"' "$file")
        if [ "$message_id" = "missing" ]; then
            error "[$idx] Missing 'message_id' field"
            issues=$((issues + 1))
        elif [ "$message_id" != "$idx" ]; then
            warn "[$idx] message_id ($message_id) doesn't match filename index ($idx)"
            issues=$((issues + 1))
        fi
        
        # Collect all tool use and result IDs
        while IFS= read -r tool_id; do
            if [ -n "$tool_id" ]; then
                tool_use_map["$tool_id"]="$idx"
            fi
        done < <(get_tool_use_ids "$file")
        
        while IFS= read -r tool_id; do
            if [ -n "$tool_id" ]; then
                tool_result_map["$tool_id"]="$idx"
            fi
        done < <(get_tool_result_ids "$file")
        
    done < <(get_message_files "$dir")
    
    # Check for orphaned tool uses
    for tool_id in "${!tool_use_map[@]}"; do
        if [ -z "${tool_result_map[$tool_id]:-}" ]; then
            error "[${tool_use_map[$tool_id]}] Orphaned tool use: $tool_id (no matching result)"
            issues=$((issues + 1))
        fi
    done
    
    # Check for orphaned tool results
    for tool_id in "${!tool_result_map[@]}"; do
        if [ -z "${tool_use_map[$tool_id]:-}" ]; then
            error "[${tool_result_map[$tool_id]}] Orphaned tool result: $tool_id (no matching use)"
            issues=$((issues + 1))
        fi
    done
    
    echo
    if [ $issues -eq 0 ]; then
        success "No issues found. Session is healthy."
        return 0
    else
        warn "Found $issues issue(s) in session"
        return 1
    fi
}

# List command
cmd_list() {
    local dir="$1"
    local verbose="${2:-false}"
    
    display_session_target "$dir"
    
    echo -e "${CYAN}IDX  ROLE       BLOCKS  TYPES                    PREVIEW${NC}"
    echo "---  ---------  ------  -----------------------  -------"
    
    while IFS= read -r file; do
        local idx
        idx=$(get_message_index "$file")
        
        local role
        role=$(jq -r '.message.role' "$file" 2>/dev/null || echo "ERROR")
        
        local block_count
        block_count=$(jq '.message.content | length' "$file" 2>/dev/null || echo "0")
        
        local types
        types=$(jq -r '.message.content[] | keys[0]' "$file" 2>/dev/null | tr '\n' ',' | sed 's/,$//' | head -c 23)
        
        local preview
        preview=$(get_message_preview "$file")
        
        printf "%-4s %-10s %-7s %-24s %s\n" "$idx" "$role" "$block_count" "$types" "$preview"
    done < <(get_message_files "$dir")
}

# Validate command
cmd_validate() {
    local dir="$1"
    
    display_session_target "$dir"
    
    info "Validating session..."
    echo
    
    local issues=0
    local total=0
    
    while IFS= read -r file; do
        total=$((total + 1))
        local idx
        idx=$(get_message_index "$file")
        
        # Check JSON validity
        if ! jq empty "$file" 2>/dev/null; then
            error "[$idx] Invalid JSON in file: $file"
            issues=$((issues + 1))
            continue
        fi
        
        # Check required top-level fields
        local message_id
        message_id=$(jq -r '.message_id // "missing"' "$file")
        if [ "$message_id" = "missing" ]; then
            error "[$idx] Missing 'message_id' field"
            issues=$((issues + 1))
        fi
        
        local created_at
        created_at=$(jq -r '.created_at // "missing"' "$file")
        if [ "$created_at" = "missing" ]; then
            error "[$idx] Missing 'created_at' field"
            issues=$((issues + 1))
        fi
        
        local updated_at
        updated_at=$(jq -r '.updated_at // "missing"' "$file")
        if [ "$updated_at" = "missing" ]; then
            error "[$idx] Missing 'updated_at' field"
            issues=$((issues + 1))
        fi
        
        # Check message structure
        local role
        role=$(jq -r '.message.role // "missing"' "$file")
        if [ "$role" = "missing" ]; then
            error "[$idx] Missing 'message.role' field"
            issues=$((issues + 1))
        elif [ "$role" != "user" ] && [ "$role" != "assistant" ]; then
            error "[$idx] Invalid role: $role (must be 'user' or 'assistant')"
            issues=$((issues + 1))
        fi
        
        # Check content array exists and is non-empty
        local content_length
        content_length=$(jq '.message.content | length' "$file" 2>/dev/null || echo "0")
        if [ "$content_length" -eq 0 ]; then
            error "[$idx] Empty or missing 'message.content' array"
            issues=$((issues + 1))
        fi
        
    done < <(get_message_files "$dir")
    
    echo
    echo "Validated $total message(s)"
    
    if [ $issues -eq 0 ]; then
        success "All messages are valid"
        return 0
    else
        error "Found $issues validation issue(s)"
        return 1
    fi
}

# Backup command
cmd_backup() {
    local dir="$1"
    local backup_dir="${2:-./session-backups}"
    
    display_session_target "$dir"
    
    # Extract session name from path
    local session_name
    session_name=$(basename "$(dirname "$(dirname "$dir")")")
    
    # Create timestamped backup directory
    local timestamp
    timestamp=$(date +%Y%m%d-%H%M%S)
    local backup_path="$backup_dir/$session_name-$timestamp"
    
    info "Creating backup: $backup_path"
    
    # Create backup directory structure
    mkdir -p "$backup_path"
    
    # Copy all message files
    local file_count=0
    while IFS= read -r file; do
        cp "$file" "$backup_path/"
        file_count=$((file_count + 1))
    done < <(get_message_files "$dir")
    
    # Calculate backup size
    local backup_size
    backup_size=$(du -sh "$backup_path" 2>/dev/null | cut -f1)
    
    echo
    success "Backup created successfully"
    echo "Location: $backup_path"
    echo "Files:    $file_count"
    echo "Size:     $backup_size"
}

# Rollback command
cmd_rollback() {
    local dir="$1"
    local num_messages="${2:-1}"
    local skip_confirm="${3:-false}"
    local backup_dir="${4:-./session-backups}"
    
    display_session_target "$dir"
    
    info "Rolling back $num_messages user message(s)..."
    echo
    
    # Find user text messages (not tool results)
    local -a user_messages=()
    while IFS= read -r file; do
        local role
        role=$(jq -r '.message.role' "$file" 2>/dev/null)
        if [ "$role" = "user" ] && message_has_content_type "$file" "text"; then
            user_messages+=("$file")
        fi
    done < <(get_message_files "$dir")
    
    if [ ${#user_messages[@]} -eq 0 ]; then
        error "No user messages found to roll back"
        exit 1
    fi
    
    if [ "$num_messages" -gt "${#user_messages[@]}" ]; then
        error "Cannot roll back $num_messages messages (only ${#user_messages[@]} user messages exist)"
        exit 1
    fi
    
    # Get the Nth-to-last user message
    local target_idx=$((${#user_messages[@]} - num_messages))
    local target_file="${user_messages[$target_idx]}"
    local cutoff_index
    cutoff_index=$(get_message_index "$target_file")
    
    # Count files to delete
    local -a files_to_delete=()
    while IFS= read -r file; do
        local idx
        idx=$(get_message_index "$file")
        if [ "$idx" -ge "$cutoff_index" ]; then
            files_to_delete+=("$file")
        fi
    done < <(get_message_files "$dir")
    
    # Show preview
    echo "Will delete ${#files_to_delete[@]} message file(s) starting from index $cutoff_index:"
    echo
    
    local preview_count=0
    for file in "${files_to_delete[@]}"; do
        local idx
        idx=$(get_message_index "$file")
        local preview
        preview=$(get_message_preview "$file")
        
        if [ "$preview_count" -lt 10 ]; then
            echo "  - message_${idx}.json: $preview"
            preview_count=$((preview_count + 1))
        fi
    done
    
    if [ ${#files_to_delete[@]} -gt 10 ]; then
        echo "  ... and $((${#files_to_delete[@]} - 10)) more"
    fi
    
    echo
    
    # Confirm
    if [ "$skip_confirm" != "true" ]; then
        read -p "Proceed with rollback? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "Rollback cancelled"
            exit 0
        fi
    fi
    
    # Create backup first
    info "Creating backup before rollback..."
    cmd_backup "$dir" "$backup_dir" > /dev/null
    
    # Delete files
    info "Deleting ${#files_to_delete[@]} message(s)..."
    for file in "${files_to_delete[@]}"; do
        rm "$file"
    done
    
    echo
    success "Rolled back $num_messages user message(s)"
    echo "Deleted ${#files_to_delete[@]} total message file(s)"
}

# Fix command
cmd_fix() {
    local dir="$1"
    local skip_confirm="${2:-false}"
    local backup_dir="${3:-./session-backups}"
    
    display_session_target "$dir"
    
    info "Analyzing session for fixable issues..."
    echo
    
    # Build map of tool uses and results
    declare -A tool_use_map
    declare -A tool_result_map
    
    while IFS= read -r file; do
        local idx
        idx=$(get_message_index "$file")
        
        # Collect tool use IDs
        while IFS= read -r tool_id; do
            if [ -n "$tool_id" ]; then
                tool_use_map["$tool_id"]="$idx"
            fi
        done < <(get_tool_use_ids "$file")
        
        # Collect tool result IDs
        while IFS= read -r tool_id; do
            if [ -n "$tool_id" ]; then
                tool_result_map["$tool_id"]="$idx"
            fi
        done < <(get_tool_result_ids "$file")
        
    done < <(get_message_files "$dir")
    
    # Find first orphaned tool use
    local first_orphan=""
    for tool_id in "${!tool_use_map[@]}"; do
        if [ -z "${tool_result_map[$tool_id]:-}" ]; then
            local idx="${tool_use_map[$tool_id]}"
            if [ -z "$first_orphan" ] || [ "$idx" -lt "$first_orphan" ]; then
                first_orphan="$idx"
            fi
        fi
    done
    
    if [ -z "$first_orphan" ]; then
        success "No orphaned tool uses found. Nothing to fix."
        return 0
    fi
    
    # Count files to delete
    local -a files_to_delete=()
    while IFS= read -r file; do
        local idx
        idx=$(get_message_index "$file")
        if [ "$idx" -ge "$first_orphan" ]; then
            files_to_delete+=("$file")
        fi
    done < <(get_message_files "$dir")
    
    # Show what will be fixed
    echo "Found orphaned tool use at message $first_orphan"
    echo "Will delete ${#files_to_delete[@]} message file(s) from index $first_orphan onwards:"
    echo
    
    local preview_count=0
    for file in "${files_to_delete[@]}"; do
        local idx
        idx=$(get_message_index "$file")
        local preview
        preview=$(get_message_preview "$file")
        
        if [ "$preview_count" -lt 10 ]; then
            echo "  - message_${idx}.json: $preview"
            preview_count=$((preview_count + 1))
        fi
    done
    
    if [ ${#files_to_delete[@]} -gt 10 ]; then
        echo "  ... and $((${#files_to_delete[@]} - 10)) more"
    fi
    
    echo
    
    # Confirm
    if [ "$skip_confirm" != "true" ]; then
        read -p "Proceed with fix? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "Fix cancelled"
            exit 0
        fi
    fi
    
    # Create backup first
    info "Creating backup before fix..."
    cmd_backup "$dir" "$backup_dir" > /dev/null
    
    # Delete files
    info "Deleting ${#files_to_delete[@]} message(s)..."
    for file in "${files_to_delete[@]}"; do
        rm "$file"
    done
    
    echo
    success "Session fixed successfully"
    echo "Deleted ${#files_to_delete[@]} message file(s) starting from index $first_orphan"
}

# Main function
main() {
    check_dependencies
    
    if [ $# -lt 1 ]; then
        usage
        exit 1
    fi
    
    local command="$1"
    
    if [ "$command" = "-h" ] || [ "$command" = "--help" ]; then
        usage
        exit 0
    fi
    
    if [ $# -lt 2 ]; then
        error "Missing session_name argument"
        usage
        exit 1
    fi
    
    local session_name="$2"
    shift 2
    
    # Parse optional agent name and options
    local agent_name=""
    local session_base="$DEFAULT_SESSION_BASE"
    local verbose=false
    local skip_confirm=false
    local backup_dir="./session-backups"
    local num_messages=1
    
    # Check if first argument is not an option (then it's agent_name)
    if [ $# -gt 0 ] && [[ ! "$1" =~ ^- ]]; then
        agent_name="$1"
        shift
    fi
    
    # Parse remaining options
    while [ $# -gt 0 ]; do
        case "$1" in
            -s|--session-base)
                if [ $# -lt 2 ]; then
                    error "Missing argument for $1"
                    exit 1
                fi
                session_base="$2"
                shift 2
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            -y|--yes)
                skip_confirm=true
                shift
                ;;
            -b|--backup-dir)
                if [ $# -lt 2 ]; then
                    error "Missing argument for $1"
                    exit 1
                fi
                backup_dir="$2"
                shift 2
                ;;
            -n|--number)
                if [ $# -lt 2 ]; then
                    error "Missing argument for $1"
                    exit 1
                fi
                num_messages="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    # Resolve session path from session name
    local resolved_dir
    resolved_dir=$(resolve_session_path "$session_name" "$agent_name" "$session_base")
    
    validate_session_dir "$resolved_dir"
    
    case "$command" in
        stats)
            cmd_stats "$resolved_dir" "$verbose"
            ;;
        diagnose)
            cmd_diagnose "$resolved_dir"
            ;;
        list)
            cmd_list "$resolved_dir" "$verbose"
            ;;
        validate)
            cmd_validate "$resolved_dir"
            ;;
        backup)
            cmd_backup "$resolved_dir" "$backup_dir"
            ;;
        rollback)
            cmd_rollback "$resolved_dir" "$num_messages" "$skip_confirm" "$backup_dir"
            ;;
        fix)
            cmd_fix "$resolved_dir" "$skip_confirm" "$backup_dir"
            ;;
        *)
            error "Unknown command: $command"
            error "Available: stats, diagnose, list, validate, backup, rollback, fix"
            exit 1
            ;;
    esac
}

main "$@"
