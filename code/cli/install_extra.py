#!/usr/bin/env python3
"""
YACBA Install Extras Subcommand

Install additional model provider extras or tools.
"""

import sys
import os
import subprocess
from pathlib import Path
from extras_discovery import discover_all_extras, get_install_command


# ANSI color codes
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'


def main():
    """Install extra packages."""
    if len(sys.argv) < 2:
        print(f"{RED}✗{NC} No extras specified", file=sys.stderr)
        print()
        print("Usage: yacba install-extras <name> [<name> ...]")
        print()
        print("Examples:")
        print("  yacba install-extras anthropic")
        print("  yacba install-extras anthropic openai litellm")
        print()
        print("To see available extras:")
        print("  yacba list-extras")
        return 1
    
    extra_names = sys.argv[1:]
    
    # Discover all available extras
    all_extras = discover_all_extras()
    available_names = {e.name for e in all_extras}
    
    # Validate all extras exist
    unknown = [name for name in extra_names if name not in available_names]
    if unknown:
        print(f"{RED}✗{NC} Unknown extras: {', '.join(unknown)}", file=sys.stderr)
        print()
        print("Available extras:")
        for extra in sorted(available_names):
            print(f"  {extra}")
        print()
        print("Run 'yacba list-extras' for more details")
        return 1
    
    # Find the venv
    yacba_home = Path(os.environ.get('YACBA_HOME', Path.home() / ".yacba"))
    venv_pip = yacba_home / ".venv" / "bin" / "pip"
    
    if not venv_pip.exists():
        print(f"{RED}✗{NC} Virtual environment not found", file=sys.stderr)
        print(f"Expected: {venv_pip}", file=sys.stderr)
        return 1
    
    # Install each extra
    installed = []
    failed = []
    
    for extra_name in extra_names:
        package_spec, pip_args = get_install_command(extra_name)
        
        print(f"{BLUE}ℹ{NC} Installing {extra_name} from {package_spec}...")
        
        try:
            subprocess.run(
                [str(venv_pip), 'install'] + pip_args + [package_spec],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            print(f"{GREEN}✓{NC} Successfully installed: {extra_name}")
            installed.append(extra_name)
        
        except subprocess.CalledProcessError as e:
            print(f"{RED}✗{NC} Failed to install: {extra_name}")
            if e.stderr:
                print(f"  Error: {e.stderr.decode().strip()}")
            failed.append(extra_name)
    
    # Summary
    print()
    print("=" * 50)
    if installed:
        print(f"{GREEN}✓{NC} Installed ({len(installed)}): {', '.join(installed)}")
    if failed:
        print(f"{RED}✗{NC} Failed ({len(failed)}): {', '.join(failed)}")
    print()
    
    if installed:
        print("Verify installation:")
        print("  yacba doctor")
    
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
