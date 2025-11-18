#!/usr/bin/env python3
"""
YACBA Upgrade Dependencies Subcommand

Upgrade all dependencies to their latest compatible versions.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from importlib import metadata


# ANSI color codes
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
BOLD = '\033[1m'
NC = '\033[0m'


def get_package_version(package):
    """Get version of installed package."""
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return None


def upgrade_core_deps(code_path, venv_python, dry_run=False):
    """Upgrade YACBA core dependencies via pip install -e --upgrade."""
    print(f"Upgrading YACBA core dependencies...")
    print()
    
    if dry_run:
        print(f"{YELLOW}ℹ{NC} Dry run - no packages will be modified")
        print()
    
    # Record current versions
    packages_to_check = [
        'yacba',
        'strands-agent-factory',
        'strands-agents',
        'repl-toolkit',
        'profile-config',
        'dataclass-args',
    ]
    
    before_versions = {}
    for pkg in packages_to_check:
        version = get_package_version(pkg)
        if version:
            before_versions[pkg] = version
    
    # Upgrade using pip install -e --upgrade
    cmd = [
        str(venv_python),
        '-m', 'pip',
        'install',
        '-e', str(code_path),
        '--upgrade'
    ]
    
    if dry_run:
        cmd.append('--dry-run')
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        if dry_run:
            print(result.stdout)
            print(f"{GREEN}✓{NC} Dry run complete")
            print()
            print("To actually upgrade, run without --dry-run:")
            print("  yacba upgrade-deps")
            return True
        
        print(f"{GREEN}✓{NC} Core dependencies upgraded")
        print()
        
        # Show what changed
        changed = []
        for pkg in packages_to_check:
            after_version = get_package_version(pkg)
            if after_version and pkg in before_versions:
                if before_versions[pkg] != after_version:
                    changed.append((pkg, before_versions[pkg], after_version))
            elif after_version and pkg not in before_versions:
                changed.append((pkg, None, after_version))
        
        if changed:
            print("Package updates:")
            for pkg, old, new in changed:
                if old:
                    print(f"  {pkg}: {old} → {BOLD}{new}{NC}")
                else:
                    print(f"  {pkg}: {BOLD}{new}{NC} (newly installed)")
        else:
            print("No package versions changed (already up to date)")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"{RED}✗{NC} Upgrade failed", file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False


def upgrade_extras(extras, code_path, venv_python, dry_run=False):
    """Upgrade optional extras using pyproject.toml extras."""
    if not extras:
        return True
    
    print(f"Upgrading extras: {', '.join(extras)}")
    print()
    
    if dry_run:
        print(f"{YELLOW}ℹ{NC} Dry run - no packages will be modified")
        print()
    
    # Extras are defined in pyproject.toml
    # pip install -e ".[extra1,extra2]" --upgrade
    
    # Record current versions for common extras packages
    packages_to_check = [
        'anthropic',
        'openai',
        'google-generativeai',
        'ollama',
        'mistralai',
        'litellm',
    ]
    
    before_versions = {pkg: get_package_version(pkg) for pkg in packages_to_check}
    
    # Build extras string
    extras_str = ','.join(extras)
    
    cmd = [
        str(venv_python),
        '-m', 'pip',
        'install',
        '-e', f"{code_path}[{extras_str}]",
        '--upgrade'
    ]
    
    if dry_run:
        cmd.append('--dry-run')
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        if dry_run:
            print(result.stdout)
            print(f"{GREEN}✓{NC} Dry run complete")
            return True
        
        print(f"{GREEN}✓{NC} Extras upgraded")
        print()
        
        # Show what changed
        changed = []
        for pkg in packages_to_check:
            after_version = get_package_version(pkg)
            if after_version:
                old = before_versions.get(pkg)
                if old and old != after_version:
                    changed.append((pkg, old, after_version))
                elif not old:
                    changed.append((pkg, None, after_version))
        
        if changed:
            print("Package updates:")
            for pkg, old, new in changed:
                if old:
                    print(f"  {pkg}: {old} → {BOLD}{new}{NC}")
                else:
                    print(f"  {pkg}: {BOLD}{new}{NC} (newly installed)")
        else:
            print("No package versions changed (already up to date)")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"{RED}✗{NC} Upgrade failed: {e}", file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False


def main():
    """Upgrade dependencies."""
    parser = argparse.ArgumentParser(
        description='Upgrade YACBA dependencies to latest versions'
    )
    parser.add_argument(
        '--extras', '-e',
        nargs='+',
        help='Upgrade specific extras (anthropic, openai, google, ollama, mistral, litellm, all)'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show what would be upgraded without making changes'
    )
    parser.add_argument(
        '--skip-core',
        action='store_true',
        help='Skip upgrading core dependencies (only upgrade extras)'
    )
    
    args = parser.parse_args()
    
    yacba_home = Path(os.environ.get('YACBA_HOME', Path.home() / ".yacba"))
    code_path = yacba_home / "code"
    venv_python = yacba_home / ".venv" / "bin" / "python3"
    
    if not venv_python.exists():
        print(f"{RED}✗{NC} Virtual environment not found", file=sys.stderr)
        print(f"Expected: {venv_python}", file=sys.stderr)
        return 1
    
    if not code_path.exists():
        print(f"{RED}✗{NC} YACBA code directory not found", file=sys.stderr)
        print(f"Expected: {code_path}", file=sys.stderr)
        return 1
    
    print("YACBA Dependency Upgrade")
    print("=" * 50)
    print()
    
    success = True
    
    # Upgrade core dependencies
    if not args.skip_core:
        if not upgrade_core_deps(code_path, venv_python, args.dry_run):
            success = False
        print()
    
    # Upgrade extras
    if args.extras:
        if not upgrade_extras(args.extras, code_path, venv_python, args.dry_run):
            success = False
        print()
    
    if success:
        if args.dry_run:
            print(f"{BLUE}ℹ{NC} Run without --dry-run to apply upgrades")
        else:
            print(f"{GREEN}✓{NC} All upgrades complete")
            print()
            print("To verify installation:")
            print("  yacba doctor")
    else:
        print(f"{RED}✗{NC} Some upgrades failed", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
