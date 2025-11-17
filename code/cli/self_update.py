#!/usr/bin/env python3
"""
YACBA Self-Update Subcommand

Update YACBA to the latest version from GitHub.
"""

import sys
import os
import subprocess
from pathlib import Path


# ANSI color codes
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'


def main():
    """Update YACBA code from git."""
    yacba_home = Path(os.environ.get('YACBA_HOME', Path.home() / ".yacba"))
    code_path = yacba_home / "code"
    
    if not (code_path / ".git").exists():
        print(f"{RED}✗{NC} Not a git repository", file=sys.stderr)
        print("Cannot auto-update. Please reinstall manually.", file=sys.stderr)
        return 1
    
    print("Updating YACBA...")
    print()
    
    try:
        # Fetch latest
        subprocess.run(
            ['git', 'fetch', 'origin', 'main'],
            cwd=code_path,
            check=True,
            capture_output=True
        )
        
        # Check if updates available
        result = subprocess.run(
            ['git', 'rev-list', '--count', 'HEAD..origin/main'],
            cwd=code_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        updates = int(result.stdout.strip())
        
        if updates == 0:
            print(f"{GREEN}✓{NC} Already up to date")
            return 0
        
        print(f"Found {updates} update(s)")
        
        # Pull updates
        subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            cwd=code_path,
            check=True
        )
        
        print()
        print(f"{GREEN}✓{NC} Update complete")
        
        # Check if dependencies need updating
        print()
        print(f"{YELLOW}⚠{NC} Check for dependency updates:")
        print("  yacba doctor")
        
        return 0
    
    except subprocess.CalledProcessError as e:
        print(f"{RED}✗{NC} Update failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
