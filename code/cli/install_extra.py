#!/usr/bin/env python3
"""
YACBA Install Extra Subcommand

Install additional model provider extras.
"""

import sys
import subprocess
import argparse
from pathlib import Path


# ANSI color codes
GREEN = '\033[0;32m'
RED = '\033[0;31m'
NC = '\033[0m'


def main():
    """Install extra packages."""
    parser = argparse.ArgumentParser(description="Install model provider extras")
    parser.add_argument('extras', nargs='+', help="Extras to install")
    args = parser.parse_args()
    
    # Validate we're in a venv
    venv_python = Path(sys.executable)
    if '.yacba' not in str(venv_python):
        print(f"{RED}✗{NC} Not running in YACBA virtual environment", file=sys.stderr)
        return 1
    
    # Build package spec
    extras_str = ','.join(args.extras)
    package_spec = f"strands-agents[{extras_str}]"
    
    print(f"Installing {package_spec}...")
    print()
    
    # Run pip install
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-q', package_spec],
            check=True
        )
        
        print(f"{GREEN}✓{NC} Installation complete")
        print()
        print("Installed extras:")
        for extra in args.extras:
            print(f"  {GREEN}✓{NC} {extra}")
        
        return 0
    
    except subprocess.CalledProcessError:
        print(f"{RED}✗{NC} Installation failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
