#!/usr/bin/env python3
"""
YACBA Version Subcommand

Display version information.
"""

import sys
import os
from pathlib import Path
from importlib import metadata


def get_git_info():
    """Get git information if available."""
    try:
        import subprocess
        yacba_home = Path(os.environ.get('YACBA_HOME', Path.home() / ".yacba"))
        code_path = yacba_home / "code"
        
        if not (code_path / ".git").exists():
            return None
        
        # Get commit hash
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=code_path,
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0:
            commit = result.stdout.strip()
            
            # Get branch
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=code_path,
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                branch = result.stdout.strip()
                return f"{branch}@{commit}"
        
        return None
    
    except Exception:
        return None


def main():
    """Display version information."""
    # YACBA version (from git or hardcoded)
    git_info = get_git_info()
    yacba_version = git_info or "development"
    
    print(f"YACBA version: {yacba_version}")
    
    # strands-agents version
    try:
        strands_version = metadata.version('strands-agents')
        print(f"strands-agents: {strands_version}")
    except metadata.PackageNotFoundError:
        print("strands-agents: not installed")
    
    # Python version
    print(f"Python: {sys.version.split()[0]}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
