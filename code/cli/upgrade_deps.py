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


def upgrade_requirements(requirements_file, venv_python, dry_run=False):
    """Upgrade packages from requirements.txt."""
    if not requirements_file.exists():
        print(f"{RED}✗{NC} requirements.txt not found: {requirements_file}", file=sys.stderr)
        return False
    
    print(f"Upgrading dependencies from requirements.txt...")
    print()
    
    if dry_run:
        print(f"{YELLOW}ℹ{NC} Dry run - no packages will be modified")
        print()
    
    # Record current versions
    packages_to_check = [
        'strands-agent-factory',
        'strands-agents',
        'repl-toolkit',
        'profile-config',
        'dataclass-args',
        'litellm',
        'anthropic',
        'openai',
        'google-generativeai',
    ]
    
    before_versions = {}
    for pkg in packages_to_check:
        version = get_package_version(pkg)
        if version:
            before_versions[pkg] = version
    
    # Upgrade
    cmd = [
        str(venv_python),
        '-m', 'pip',
        'install',
        '--upgrade',
        '-r', str(requirements_file)
    ]
    
    if dry_run:
        cmd.append('--dry-run')
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=not dry_run,
            text=True
        )
        
        if dry_run:
            print(f"{GREEN}✓{NC} Dry run complete")
            print()
            print("To actually upgrade, run without --dry-run:")
            print("  yacba upgrade-deps")
            return True
        
        print(f"{GREEN}✓{NC} Dependencies upgraded")
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
        if dry_run:
            print(str(e), file=sys.stderr)
        return False


def upgrade_extras(extras, venv_python, dry_run=False):
    """Upgrade optional extras."""
    if not extras:
        return True
    
    print(f"Upgrading extras: {', '.join(extras)}")
    print()
    
    if dry_run:
        print(f"{YELLOW}ℹ{NC} Dry run - no packages will be modified")
        print()
    
    # Map extras to packages
    extras_map = {
        'anthropic': ['anthropic'],
        'openai': ['openai'],
        'google': ['google-generativeai'],
        'ollama': ['ollama'],
        'mistral': ['mistralai'],
        'litellm': ['litellm'],
        'all': ['anthropic', 'openai', 'google-generativeai', 'ollama', 'mistralai', 'litellm'],
    }
    
    packages = []
    for extra in extras:
        if extra in extras_map:
            packages.extend(extras_map[extra])
        else:
            print(f"{YELLOW}⚠{NC} Unknown extra: {extra} (skipping)")
    
    if not packages:
        return True
    
    # Remove duplicates
    packages = list(set(packages))
    
    # Record current versions
    before_versions = {pkg: get_package_version(pkg) for pkg in packages}
    
    cmd = [
        str(venv_python),
        '-m', 'pip',
        'install',
        '--upgrade'
    ] + packages
    
    if dry_run:
        cmd.append('--dry-run')
    
    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=not dry_run,
            text=True
        )
        
        if dry_run:
            print(f"{GREEN}✓{NC} Dry run complete")
            return True
        
        print(f"{GREEN}✓{NC} Extras upgraded")
        print()
        
        # Show what changed
        changed = []
        for pkg in packages:
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
        '--skip-requirements',
        action='store_true',
        help='Skip upgrading requirements.txt (only upgrade extras)'
    )
    
    args = parser.parse_args()
    
    yacba_home = Path(os.environ.get('YACBA_HOME', Path.home() / ".yacba"))
    venv_python = yacba_home / ".venv" / "bin" / "python3"
    requirements_file = yacba_home / "code" / "requirements.txt"
    
    if not venv_python.exists():
        print(f"{RED}✗{NC} Virtual environment not found", file=sys.stderr)
        print(f"Expected: {venv_python}", file=sys.stderr)
        return 1
    
    print("YACBA Dependency Upgrade")
    print("=" * 50)
    print()
    
    success = True
    
    # Upgrade requirements.txt
    if not args.skip_requirements:
        if not upgrade_requirements(requirements_file, venv_python, args.dry_run):
            success = False
        print()
    
    # Upgrade extras
    if args.extras:
        if not upgrade_extras(args.extras, venv_python, args.dry_run):
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
