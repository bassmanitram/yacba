#!/usr/bin/env python3
"""
YACBA Link Subcommand

Create symlinks to the yacba launcher for easy command-line access.
"""

import sys
import os
import argparse
from pathlib import Path


def find_yacba_launcher():
    """Find the installed yacba launcher script."""
    yacba_home = Path(os.environ.get("YACBA_HOME", Path.home() / ".yacba"))
    launcher = yacba_home / "code" / "yacba"
    
    if not launcher.exists():
        print(f"✗ YACBA launcher not found at: {launcher}", file=sys.stderr)
        print("  Run 'yacba install' first.", file=sys.stderr)
        return None
    
    return launcher


def get_path_dirs():
    """Get directories in PATH with permission status."""
    path_env = os.environ.get("PATH", "")
    dirs = []
    
    for dir_str in path_env.split(":"):
        if not dir_str:
            continue
        dir_path = Path(dir_str)
        if dir_path.exists():
            writable = os.access(dir_path, os.W_OK)
            dirs.append((dir_path, writable))
    
    return dirs


def find_best_location():
    """Find the best default location for symlink."""
    path_dirs = get_path_dirs()
    
    # First: writable directories in PATH
    for dir_path, writable in path_dirs:
        if writable:
            return dir_path
    
    # Second: common user directories (create if needed)
    for candidate in [Path.home() / "bin", Path.home() / ".local" / "bin"]:
        if candidate.exists() or not (Path("/usr/local/bin").exists()):
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
    
    # Last resort
    return Path("/usr/local/bin")


def check_needs_sudo(target_dir):
    """Check if target directory needs elevated permissions."""
    return not os.access(target_dir, os.W_OK)


def create_symlink(target, link_path, force=False, quiet=False):
    """Create a symlink with proper error handling."""
    
    # Check if link already exists
    if link_path.exists() or link_path.is_symlink():
        if link_path.is_symlink():
            existing_target = link_path.resolve()
            if existing_target == target:
                if not quiet:
                    print(f"✓ Symlink already points to correct target: {link_path}")
                return 0
            
            if not force:
                print(f"⚠ Symlink exists: {link_path}")
                print(f"  Currently points to: {existing_target}")
                response = input("Overwrite? [y/N]: ").strip().lower()
                if response not in ['y', 'yes']:
                    print("Cancelled.")
                    return 1
        else:
            if not force:
                print(f"⚠ File exists: {link_path}")
                response = input("Overwrite? [y/N]: ").strip().lower()
                if response not in ['y', 'yes']:
                    print("Cancelled.")
                    return 1
        
        # Remove existing
        link_path.unlink()
    
    # Check permissions
    if check_needs_sudo(link_path.parent):
        print(f"⚠ {link_path.parent} requires elevated permissions")
        response = input("Use sudo to create symlink? [y/N]: ").strip().lower()
        
        if response in ['y', 'yes']:
            import subprocess
            cmd = ["sudo", "ln", "-sf", str(target), str(link_path)]
            result = subprocess.run(cmd)
            if result.returncode == 0:
                if not quiet:
                    print(f"✓ Symlink created: {link_path}")
                return 0
            else:
                print("✗ Failed to create symlink", file=sys.stderr)
                return 1
        else:
            print()
            print("Run this command manually:")
            print(f"  sudo ln -sf {target} {link_path}")
            print()
            print(f"Or choose a different location: yacba link {Path.home() / 'bin'}")
            return 1
    
    # Create symlink
    try:
        link_path.symlink_to(target)
        if not quiet:
            print(f"✓ Symlink created: {link_path}")
        return 0
    except Exception as e:
        print(f"✗ Failed to create symlink: {e}", file=sys.stderr)
        return 1


def list_locations():
    """List available PATH locations."""
    print("Directories in your PATH:\n")
    
    path_dirs = get_path_dirs()
    writable = [d for d, w in path_dirs if w]
    readonly = [d for d, w in path_dirs if not w]
    
    if writable:
        print("Writable (no sudo needed):")
        for dir_path in writable:
            print(f"  {dir_path}")
        print()
    
    if readonly:
        print("Requires elevated permissions:")
        for dir_path in readonly:
            print(f"  {dir_path}")
        print()
    
    print("You can specify any directory, even if not in PATH.")


def main():
    parser = argparse.ArgumentParser(
        description="Create a symlink to the yacba launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  yacba link                           # Auto-detect best location
  yacba link /usr/local/bin            # Install to specific location
  yacba link --name yacba-dev          # Custom name
  yacba link /home/user/bin --name ya  # Both custom
  yacba link --list                    # Show available locations
        """
    )
    
    parser.add_argument(
        "path",
        nargs="?",
        help="Target directory (default: first writable in PATH)"
    )
    parser.add_argument(
        "--name",
        default="yacba",
        help="Symlink name (default: yacba)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing file/symlink without prompting"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available PATH locations"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_locations()
        return 0
    
    # Find launcher
    target = find_yacba_launcher()
    if not target:
        return 1
    
    # Determine target directory
    if args.path:
        target_dir = Path(args.path)
        if not target_dir.exists():
            print(f"✗ Directory does not exist: {target_dir}", file=sys.stderr)
            return 1
        if not target_dir.is_dir():
            print(f"✗ Not a directory: {target_dir}", file=sys.stderr)
            return 1
    else:
        target_dir = find_best_location()
    
    link_path = target_dir / args.name
    
    # Check if target_dir is in PATH
    path_dirs = [str(d) for d, _ in get_path_dirs()]
    if str(target_dir) not in path_dirs and not args.quiet:
        print(f"⚠ Warning: {target_dir} is not in your PATH")
        print(f"\nTo use '{args.name}' from anywhere, add to your shell profile:")
        print(f'  export PATH="{target_dir}:$PATH"')
        print()
    
    return create_symlink(target, link_path, force=args.force, quiet=args.quiet)


if __name__ == "__main__":
    sys.exit(main())
