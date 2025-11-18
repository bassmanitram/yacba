#!/usr/bin/env python3
"""
YACBA Uninstall Subcommand

Remove YACBA installation.
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path


# ANSI color codes
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
NC = "\033[0m"


def find_symlinks_to_launcher(yacba_home: Path):
    """Find all symlinks in PATH that point to our launcher."""
    launcher = yacba_home / "code" / "yacba"
    symlinks = []

    path_env = os.environ.get("PATH", "")
    for dir_str in path_env.split(":"):
        if not dir_str:
            continue
        dir_path = Path(dir_str)
        if not dir_path.exists():
            continue

        try:
            for item in dir_path.iterdir():
                if item.is_symlink():
                    try:
                        if item.resolve() == launcher.resolve():
                            symlinks.append(item)
                    except (OSError, RuntimeError):
                        pass
        except PermissionError:
            pass

    return symlinks


def remove_symlink(symlink_path: Path):
    """Remove a symlink, handling permissions."""
    try:
        symlink_path.unlink()
        print(f"{GREEN}✓{NC} Removed symlink: {symlink_path}")
        return True
    except PermissionError:
        print(f"{YELLOW}⚠{NC} {symlink_path} requires elevated permissions")
        response = input("Use sudo to remove? [y/N]: ").strip().lower()
        if response in ["y", "yes"]:
            result = subprocess.run(["sudo", "rm", str(symlink_path)])
            if result.returncode == 0:
                print(f"{GREEN}✓{NC} Removed symlink: {symlink_path}")
                return True
            else:
                print(f"{RED}✗{NC} Failed to remove symlink", file=sys.stderr)
                return False
        else:
            print(f"  Please remove manually: sudo rm {symlink_path}")
            return False
    except Exception as e:
        print(f"{RED}✗{NC} Failed to remove symlink: {e}", file=sys.stderr)
        return False


def create_cleanup_script(yacba_home: Path):
    """Create a script that will delete YACBA_HOME after we exit."""
    cleanup_script = f"""#!/bin/bash
sleep 0.5
rm -rf '{yacba_home}' 2>/dev/null || true
rm -- "$0" 2>/dev/null || true
"""
    script_path = Path(f"/tmp/.yacba_cleanup_{os.getpid()}.sh")
    script_path.write_text(cleanup_script)
    script_path.chmod(0o755)
    return script_path


def main():
    """Uninstall YACBA."""
    yacba_home = Path(os.environ.get("YACBA_HOME", Path.home() / ".yacba"))

    if not yacba_home.exists():
        print(f"{YELLOW}⚠{NC} YACBA not installed at: {yacba_home}")
        return 0

    print()
    print("═" * 50)
    print("Uninstall YACBA")
    print("═" * 50)
    print()
    print(f"This will remove: {yacba_home}")

    # Find symlinks
    symlinks = find_symlinks_to_launcher(yacba_home)
    if symlinks:
        print()
        print("Found symlinks to remove:")
        for symlink in symlinks:
            print(f"  • {symlink}")

    print()
    response = input("Continue? [y/N]: ").strip().lower()

    if response != "y":
        print("Uninstall cancelled")
        return 0

    print()
    print("Removing YACBA...")
    print()

    # Remove symlinks first
    all_removed = True
    for symlink in symlinks:
        if not remove_symlink(symlink):
            all_removed = False

    if symlinks and not all_removed:
        print()
        print(f"{YELLOW}⚠{NC} Some symlinks could not be removed automatically.")
        print("  The installation will still be removed.")
        print()

    # Check if we're running from the install location
    try:
        current_script = Path(__file__).resolve()
        running_from_install = yacba_home in current_script.parents
    except Exception:
        running_from_install = False

    if running_from_install:
        # Create cleanup script to delete after we exit
        cleanup_script = create_cleanup_script(yacba_home)
        print(f"{GREEN}✓{NC} Installation will be removed when script exits")
        print()
        print("YACBA has been uninstalled.")
        print()

        # Execute cleanup script and exit
        os.execl(str(cleanup_script), str(cleanup_script))
    else:
        # Safe to delete immediately
        try:
            shutil.rmtree(yacba_home)
            print(f"{GREEN}✓{NC} YACBA installation removed")
            print()
            print("YACBA has been uninstalled.")
            print()
            return 0
        except Exception as e:
            print(f"{RED}✗{NC} Failed to remove YACBA: {e}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    sys.exit(main())
