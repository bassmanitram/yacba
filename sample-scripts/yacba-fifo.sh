#!/bin/bash
# yacba-fifo.sh — explanatory header
#
# Purpose:
#   Run the 'yacba' binary with a named FIFO as its stdin and route its stdout
#   into a simple processor that can dynamically switch output files.
#
# How it works:
#   - A unique FIFO in /tmp is created for this script's runtime.
#   - yacba is started with the FIFO as stdin; its stdout is piped into a
#     shell function that reads lines and appends them to a target file.
#   - Any line that begins with "OUTPUT <path>" causes the processor to switch
#     the current target file to <path>. Subsequent lines are appended there.
#   - A default output file is used until an explicit OUTPUT directive is seen.
#   - To send data to the LLM, include "/send" on its own line after your input.
#   - To clear the LLM context, include "/clear" on its own line (you probably want
#     to do this in each input cycle to prevent context corruption).
#   - Either your system prompt or your input must cause the LLM to produce start
#     its output with 'OUTPUT <path>' to set the output file.
#   - It is probably best to throttle input (e.g. sleep between each cycle, or await the
#     output file containing content) to avoid overwhelming the LLM.
#
# Usage:
#   ./yacba-fifo.sh [yacba-options]
#   Then write input into the FIFO (for example from another process or via
#   redirection), e.g.:
#     echo "some input" > /tmp/yacba_fifo_<pid>
#
# Safety & cleanup:
#   - The script installs traps for EXIT/INT/TERM to remove the FIFO and kill
#     lingering background jobs, ensuring no leftover named pipes.
#   - The script enables stricter shell behavior later (set -euo pipefail).
#
# Notes:
#   - Files are opened in append mode; existing contents are preserved.
#   - The FIFO name embeds the script PID to avoid collisions.
set -euo pipefail

# Configuration
FIFO_PATH="/tmp/yacba_fifo_$$"
DEFAULT_OUTPUT="output.txt"
CURRENT_OUTPUT=""

# Cleanup function
cleanup() {
    if [[ -p "$FIFO_PATH" ]]; then
        rm -f "$FIFO_PATH"
    fi
    # Kill background jobs
    jobs -p | xargs -r kill 2>/dev/null || true
}

trap cleanup EXIT INT TERM

# Create FIFO
mkfifo "$FIFO_PATH"

# Function to process yacba output
process_output() {
    local output_file="$DEFAULT_OUTPUT"
    
    while IFS= read -r line; do
        # Check if line starts with "OUTPUT "
        if [[ "$line" =~ ^OUTPUT[[:space:]](.+)$ ]]; then
            # Extract filepath from the line
            output_file="${BASH_REMATCH[1]}"
            echo "Switching output to: $output_file" >&2
            continue
        fi
        
        # Write to current output file
        echo "$line" >> "$output_file"
    done
}

# Start yacba with FIFO as stdin, pipe stdout to processor
yacba -H "$@" < "$FIFO_PATH" | process_output &
YACBA_PID=$!

echo "yacba process started (PID: $YACBA_PID)" >&2
echo "FIFO created at: $FIFO_PATH" >&2
echo "Ready to accept input" >&2

# Example usage: read from stdin and write to FIFO
# In practice, you'd connect your data source here
#while IFS= read -r line; do
#    echo "$line" > "$FIFO_PATH"
#done

# Wait for yacba to complete
wait "$YACBA_PID"

echo "Processing complete" >&2
