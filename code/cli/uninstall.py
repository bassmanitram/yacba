#!/usr/bin/env python3
"""
YACBA Uninstall Subcommand

Remove YACBA installation.
"""

import sys
import os
import shutil
from pathlib import Path


# ANSI color codes
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'


def main():
    """Uninstall YACBA."""
    yacba_home = Path(os.environ.get('YACBA_HOME', Path.home() / ".yacba"))
    
    if not yacba_home.exists():
        print(f"{YELLOW}⚠{NC} YACBA not installed at: {yacba_home}")
        return 0
    
    print("Uninstall YACBA")
    print("=" * 50)
    print()
    print(f"This will remove: {yacba_home}")
    print()
    
    response = input("Are you sure? [y/N]: ").strip().lower()
    
    if response != 'y':
        print("Uninstall cancelled")
        return 0
    
    print()
    print("Removing YACBA...")
    
    try:
        shutil.rmtree(yacba_home)
        print(f"{GREEN}✓{NC} YACBA removed")
        print()
        print("You can now delete the yacba wrapper script if desired.")
        return 0
    
    except Exception as e:
        print(f"{RED}✗{NC} Failed to remove YACBA: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
