#!/usr/bin/env python3
"""
YACBA Version Subcommand

Display version information.
"""

import sys
import os
from pathlib import Path
from importlib import metadata


def get_version_info():
    """Get YACBA version information."""
    yacba_home = Path(os.environ.get("YACBA_HOME", Path.home() / ".yacba"))
    code_path = yacba_home / "code"

    # Try to read from package metadata
    try:
        yacba_version = metadata.version("yacba")
    except metadata.PackageNotFoundError:
        yacba_version = None

    # Try to read commit info (from download)
    commit_file = code_path / ".commit_info"
    commit_info = None

    if commit_file.exists():
        try:
            import json

            with open(commit_file, "r") as f:
                commit_info = json.load(f)
        except:
            pass

    # Try to read version from __version__.py
    version_file = code_path / "__version__.py"
    if not yacba_version and version_file.exists():
        try:
            with open(version_file, "r") as f:
                for line in f:
                    if line.startswith("__version__"):
                        yacba_version = line.split("=")[1].strip().strip("\"'")
                        break
        except:
            pass

    return {
        "version": yacba_version or "unknown",
        "commit_info": commit_info,
    }


def main():
    """Display version information."""
    info = get_version_info()

    # YACBA version
    print(f"YACBA version: {info['version']}")

    # Commit info if available
    if info["commit_info"]:
        commit = info["commit_info"]
        print(f"  Commit: {commit['short_sha']}")
        print(f"  Date: {commit['date']}")
        print(f"  Message: {commit['message']}")

    print()

    # Core dependencies
    print("Core Dependencies:")

    packages = [
        "strands-agent-factory",
        "strands-agents",
        "repl-toolkit",
        "profile-config",
        "dataclass-args",
    ]

    for package in packages:
        try:
            version = metadata.version(package)
            print(f"  {package}: {version}")
        except metadata.PackageNotFoundError:
            print(f"  {package}: not installed")

    print()

    # Python version
    print(f"Python: {sys.version.split()[0]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
