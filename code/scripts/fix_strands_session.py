#!/usr/bin/env python3
"""
Fix corrupted strands_agent sessions by removing orphaned toolUse messages.

A session is corrupted when it contains a toolUse message without a corresponding
toolResult message. This script finds such orphans and removes them along with all
subsequent messages to restore valid conversation state.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional


def find_messages_dir(session_path: Path) -> Optional[Path]:
    """Find the messages directory within a session."""
    # Look for agents/*/messages pattern
    messages_dirs = list(session_path.glob("agents/*/messages"))
    if not messages_dirs:
        return None
    if len(messages_dirs) > 1:
        print(f"Warning: Multiple message directories found in {session_path}")
        print("Using first one:", messages_dirs[0])
    return messages_dirs[0]


def find_orphaned_tooluse(messages_dir: Path) -> Optional[int]:
    """
    Scan messages for orphaned toolUse blocks.

    Returns the message_id of the first orphaned toolUse, or None if clean.
    """
    message_files = sorted(
        messages_dir.glob("message_*.json"), key=lambda f: int(f.stem.split("_")[1])
    )

    if not message_files:
        return None

    pending_tool_uses: Dict[str, int] = {}

    for msg_file in message_files:
        try:
            with open(msg_file) as f:
                data = json.load(f)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not parse {msg_file}: {e}")
            continue

        msg_id = data["message_id"]
        role = data["message"]["role"]
        content = data["message"]["content"]

        # Track toolUse in assistant messages
        if role == "assistant":
            for item in content:
                if "toolUse" in item:
                    tool_use_id = item["toolUse"]["toolUseId"]
                    pending_tool_uses[tool_use_id] = msg_id

        # Match toolResult in user messages
        if role == "user":
            for item in content:
                if "toolResult" in item:
                    tool_use_id = item["toolResult"]["toolUseId"]
                    pending_tool_uses.pop(tool_use_id, None)

    # Return the earliest orphaned message
    if pending_tool_uses:
        return min(pending_tool_uses.values())

    return None


def count_messages_from(messages_dir: Path, from_id: int) -> int:
    """Count how many messages exist from from_id onwards."""
    return len(
        [
            f
            for f in messages_dir.glob("message_*.json")
            if int(f.stem.split("_")[1]) >= from_id
        ]
    )


def delete_messages_from(
    messages_dir: Path, from_id: int, dry_run: bool = False
) -> int:
    """Delete all messages from from_id onwards. Returns count deleted."""
    to_delete = [
        f
        for f in messages_dir.glob("message_*.json")
        if int(f.stem.split("_")[1]) >= from_id
    ]

    to_delete.sort(key=lambda f: int(f.stem.split("_")[1]))

    for msg_file in to_delete:
        if dry_run:
            print(f"  Would delete: {msg_file.name}")
        else:
            msg_file.unlink()

    return len(to_delete)


def fix_session(session_path: Path, dry_run: bool = False) -> bool:
    """
    Fix a single session by removing orphaned toolUse and subsequent messages.

    Returns True if session was fixed, False if clean or error.
    """
    session_path = Path(session_path)

    if not session_path.is_dir():
        print(f"Error: {session_path} is not a directory")
        return False

    # Find messages directory
    messages_dir = find_messages_dir(session_path)
    if not messages_dir:
        print(f"Error: No messages directory found in {session_path}")
        return False

    print(f"\nChecking: {session_path.name}")
    print(f"Messages: {messages_dir}")

    # Find orphaned toolUse
    orphan_id = find_orphaned_tooluse(messages_dir)

    if orphan_id is None:
        print("✓ Session is clean (no orphaned toolUse messages)")
        return False

    # Count messages to delete
    num_to_delete = count_messages_from(messages_dir, orphan_id)

    print("\n⚠ CORRUPTION DETECTED:")
    print(f"  Orphaned toolUse at message {orphan_id}")
    print(
        f"  {num_to_delete} message(s) will be deleted (message_{orphan_id}.json onwards)"
    )

    if dry_run:
        print("\n[DRY RUN - no files will be deleted]")
        delete_messages_from(messages_dir, orphan_id, dry_run=True)
        return False

    # Ask for confirmation
    response = (
        input(f"\nDelete these {num_to_delete} message(s)? [y/N]: ").strip().lower()
    )

    if response == "y":
        deleted = delete_messages_from(messages_dir, orphan_id, dry_run=False)
        print(f"✓ Deleted {deleted} message(s)")
        return True
    else:
        print("✗ Skipped (no changes made)")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Fix corrupted strands_agent sessions by removing orphaned toolUse messages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check a single session
  %(prog)s ./session_yacba-1
  
  # Dry run to see what would be deleted
  %(prog)s --dry-run ./session_yacba-1
  
  # Check all sessions in current directory
  %(prog)s session_*
        """,
    )

    parser.add_argument(
        "sessions", nargs="+", help="Session directory/directories to check and fix"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )

    args = parser.parse_args()

    fixed_count = 0
    error_count = 0

    for session_path in args.sessions:
        try:
            if fix_session(session_path, dry_run=args.dry_run):
                fixed_count += 1
        except Exception as e:
            print(f"Error processing {session_path}: {e}")
            error_count += 1

    print(f"\n{'=' * 60}")
    print(f"Summary: {fixed_count} session(s) fixed, {error_count} error(s)")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
