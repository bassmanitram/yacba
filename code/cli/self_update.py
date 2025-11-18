#!/usr/bin/env python3
"""
YACBA Self-Update Subcommand

Update YACBA to the latest version from GitHub (no git required).
"""

import sys
import os
import shutil
from pathlib import Path
from downloader import download_github_archive, get_latest_commit_info, get_local_commit_info, DownloadError


# ANSI color codes
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'


def check_for_updates(code_path: Path) -> dict:
    """
    Check if updates are available.
    
    Returns:
        Dict with 'available', 'local_commit', 'remote_commit'
    """
    # Get local commit info
    local_info = get_local_commit_info(code_path)
    
    # Get remote commit info
    remote_info = get_latest_commit_info("bassmanitram", "yacba", "main")
    
    if not remote_info:
        return {
            'available': None,  # Unknown
            'local_commit': local_info,
            'remote_commit': None,
        }
    
    if not local_info:
        # No local commit info (old installation or manual install)
        return {
            'available': True,  # Assume update available
            'local_commit': None,
            'remote_commit': remote_info,
        }
    
    # Compare SHAs
    available = local_info['sha'] != remote_info['sha']
    
    return {
        'available': available,
        'local_commit': local_info,
        'remote_commit': remote_info,
    }


def perform_update(code_path: Path, backup: bool = True) -> bool:
    """
    Download and install update.
    
    Args:
        code_path: Path to ~/.yacba/code
        backup: Whether to create backup before updating
    
    Returns:
        True if successful, False otherwise
    """
    backup_path = code_path.parent / "code.backup"
    
    try:
        # Create backup
        if backup and code_path.exists():
            print(f"{BLUE}ℹ{NC} Creating backup...")
            if backup_path.exists():
                shutil.rmtree(backup_path)
            shutil.copytree(code_path, backup_path)
            print(f"{GREEN}✓{NC} Backup created at {backup_path}")
            print()
        
        # Download new version
        print(f"{BLUE}ℹ{NC} Downloading latest version...")
        print()
        
        result = download_github_archive(
            "bassmanitram",
            "yacba",
            code_path,
            branch="main",
            show_progress=True
        )
        
        print()
        print(f"{GREEN}✓{NC} Update complete!")
        
        if result.get('commit_info'):
            commit = result['commit_info']
            print(f"  Version: {commit['short_sha']}")
            print(f"  Message: {commit['message']}")
        
        # Remove backup on success
        if backup and backup_path.exists():
            shutil.rmtree(backup_path)
        
        return True
        
    except DownloadError as e:
        print(f"{RED}✗{NC} Update failed: {e}", file=sys.stderr)
        
        # Restore backup if available
        if backup and backup_path.exists():
            print(f"{YELLOW}⚠{NC} Restoring from backup...", file=sys.stderr)
            if code_path.exists():
                shutil.rmtree(code_path)
            shutil.move(backup_path, code_path)
            print(f"{GREEN}✓{NC} Restored from backup", file=sys.stderr)
        
        return False
    
    except Exception as e:
        print(f"{RED}✗{NC} Unexpected error: {e}", file=sys.stderr)
        
        # Restore backup if available
        if backup and backup_path.exists():
            print(f"{YELLOW}⚠{NC} Restoring from backup...", file=sys.stderr)
            try:
                if code_path.exists():
                    shutil.rmtree(code_path)
                shutil.move(backup_path, code_path)
                print(f"{GREEN}✓{NC} Restored from backup", file=sys.stderr)
            except:
                print(f"{RED}✗{NC} Failed to restore backup", file=sys.stderr)
                print(f"  Backup is at: {backup_path}", file=sys.stderr)
        
        return False


def main():
    """Update YACBA from GitHub."""
    yacba_home = Path(os.environ.get('YACBA_HOME', Path.home() / ".yacba"))
    code_path = yacba_home / "code"
    
    if not code_path.exists():
        print(f"{RED}✗{NC} YACBA code directory not found: {code_path}", file=sys.stderr)
        print("Run 'yacba install' first.", file=sys.stderr)
        return 1
    
    print("YACBA Self-Update")
    print("=" * 50)
    print()
    
    # Check for updates
    print("Checking for updates...")
    update_info = check_for_updates(code_path)
    
    if update_info['available'] is None:
        print(f"{YELLOW}⚠{NC} Could not check for updates (network error?)")
        print()
        response = input("Continue with update anyway? [y/N]: ").strip().lower()
        if response not in ['y', 'yes']:
            print("Cancelled.")
            return 0
    
    elif update_info['available'] is False:
        print(f"{GREEN}✓{NC} Already up to date!")
        
        if update_info['local_commit']:
            commit = update_info['local_commit']
            print(f"  Current: {commit['short_sha']} - {commit['message']}")
        
        print()
        print("To force update anyway:")
        print("  (Useful if files were modified or corrupted)")
        print()
        response = input("Force update? [y/N]: ").strip().lower()
        
        if response not in ['y', 'yes']:
            return 0
    
    else:
        print(f"{YELLOW}⚠{NC} Update available!")
        print()
        
        if update_info['local_commit']:
            local = update_info['local_commit']
            print(f"  Current:  {local['short_sha']} - {local['message']}")
        else:
            print(f"  Current:  Unknown version")
        
        if update_info['remote_commit']:
            remote = update_info['remote_commit']
            print(f"  Latest:   {remote['short_sha']} - {remote['message']}")
        
        print()
    
    # Perform update
    success = perform_update(code_path, backup=True)
    
    if success:
        print()
        print("Update successful! Changes are immediately active.")
        print()
        print("To verify:")
        print("  yacba version")
        print("  yacba doctor")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
