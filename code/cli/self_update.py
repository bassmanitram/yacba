#!/usr/bin/env python3
"""
YACBA Self-Update Subcommand

Update YACBA to the latest version from GitHub (no git required).
"""

import sys
import os
import shutil
import subprocess
import tarfile
import json
import urllib.request
from pathlib import Path
from typing import Optional, Dict, Any


# ANSI color codes
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"


class UpdateError(Exception):
    """Update operation failed."""

    pass


def detect_download_tool() -> Optional[str]:
    """Detect available download tool (curl or wget)."""
    if shutil.which("curl"):
        return "curl"
    elif shutil.which("wget"):
        return "wget"
    return None


def download_file(url: str, output_path: Path) -> None:
    """
    Download file using curl or wget.

    Args:
        url: URL to download
        output_path: Destination file path

    Raises:
        UpdateError: If download fails
    """
    tool = detect_download_tool()
    if tool is None:
        raise UpdateError("Neither curl nor wget found")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        if tool == "curl":
            subprocess.run(
                ["curl", "-L", "-o", str(output_path), url],
                check=True,
                capture_output=True,
            )
        elif tool == "wget":
            subprocess.run(
                ["wget", "-O", str(output_path), url], check=True, capture_output=True
            )
    except subprocess.CalledProcessError as e:
        raise UpdateError(f"Download failed: {e}")


def get_latest_commit_info(
    repo_owner: str, repo_name: str, branch: str = "main"
) -> Optional[Dict[str, Any]]:
    """
    Get latest commit information from GitHub API.

    Args:
        repo_owner: Repository owner
        repo_name: Repository name
        branch: Branch name

    Returns:
        Dict with commit info or None if failed
    """
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{branch}"

    try:
        req = urllib.request.Request(api_url)
        req.add_header("Accept", "application/vnd.github.v3+json")

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            return {
                "sha": data["sha"],
                "short_sha": data["sha"][:7],
                "message": data["commit"]["message"].split("\n")[0],
                "date": data["commit"]["committer"]["date"],
                "author": data["commit"]["author"]["name"],
            }
    except Exception:
        return None


def get_local_commit_info(code_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Get commit info for locally installed code.

    Args:
        code_dir: Directory containing .commit_info file

    Returns:
        Dict with commit info or None
    """
    commit_file = code_dir / ".commit_info"
    if not commit_file.exists():
        return None

    try:
        with open(commit_file, "r") as f:
            return json.load(f)
    except Exception:
        return None


def extract_tarball(
    tar_path: Path, extract_to: Path, strip_components: int = 1
) -> None:
    """
    Extract tarball, stripping top-level directory.

    Args:
        tar_path: Path to .tar.gz file
        extract_to: Directory to extract into
        strip_components: Number of leading path components to strip

    Raises:
        UpdateError: If extraction fails
    """
    try:
        extract_to.mkdir(parents=True, exist_ok=True)

        with tarfile.open(tar_path, "r:gz") as tar:
            members = tar.getmembers()

            if strip_components > 0:
                for member in members:
                    parts = Path(member.name).parts
                    if len(parts) > strip_components:
                        member.name = str(Path(*parts[strip_components:]))
                        tar.extract(member, extract_to)
            else:
                tar.extractall(extract_to)

    except Exception as e:
        raise UpdateError(f"Extraction failed: {e}")


def download_github_archive(
    repo_owner: str, repo_name: str, target_dir: Path, branch: str = "main"
) -> Dict[str, Any]:
    """
    Download and extract GitHub repository archive.

    Args:
        repo_owner: Repository owner
        repo_name: Repository name
        target_dir: Target directory for extracted content
        branch: Branch to download

    Returns:
        Dict with download info (commit sha, etc.)

    Raises:
        UpdateError: If download or extraction fails
    """
    archive_url = f"https://github.com/{repo_owner}/{repo_name}/archive/refs/heads/{branch}.tar.gz"

    temp_dir = Path("/tmp") / f"yacba-update-{os.getpid()}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_tar = temp_dir / f"{repo_name}.tar.gz"

    try:
        # Get commit info
        print("Fetching latest commit info...")
        commit_info = get_latest_commit_info(repo_owner, repo_name, branch)

        # Download
        print("Downloading from GitHub...")
        download_file(archive_url, temp_tar)

        size_mb = temp_tar.stat().st_size / (1024 * 1024)
        print(f"Downloaded {size_mb:.1f} MB")

        # Extract
        print("Extracting...")

        if target_dir.exists():
            shutil.rmtree(target_dir)

        extract_tarball(temp_tar, target_dir, strip_components=1)

        # Save commit info
        if commit_info:
            commit_file = target_dir / ".commit_info"
            with open(commit_file, "w") as f:
                json.dump(commit_info, f, indent=2)

        return {
            "success": True,
            "target_dir": target_dir,
            "commit_info": commit_info,
        }

    finally:
        # Cleanup
        if temp_tar.exists():
            temp_tar.unlink()
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def check_for_updates(repo_path: Path) -> dict:
    """
    Check if updates are available.

    Returns:
        Dict with 'available', 'local_commit', 'remote_commit'
    """
    local_info = get_local_commit_info(repo_path)
    remote_info = get_latest_commit_info("bassmanitram", "yacba", "main")

    if not remote_info:
        return {
            "available": None,
            "local_commit": local_info,
            "remote_commit": None,
        }

    if not local_info:
        return {
            "available": True,
            "local_commit": None,
            "remote_commit": remote_info,
        }

    available = local_info["sha"] != remote_info["sha"]

    return {
        "available": available,
        "local_commit": local_info,
        "remote_commit": remote_info,
    }


def perform_update(repo_path: Path, backup: bool = True) -> bool:
    """
    Download and install update.

    Args:
        repo_path: Path to ~/.yacba/repo
        backup: Whether to create backup before updating

    Returns:
        True if successful, False otherwise
    """
    backup_path = repo_path.parent / "repo.backup"

    try:
        # Create backup
        if backup and repo_path.exists():
            print(f"{BLUE}ℹ{NC} Creating backup...")
            if backup_path.exists():
                shutil.rmtree(backup_path)
            shutil.copytree(repo_path, backup_path, symlinks=True)
            print(f"{GREEN}✓{NC} Backup created at {backup_path}")
            print()

        # Download new version
        print(f"{BLUE}ℹ{NC} Downloading latest version...")
        print()

        result = download_github_archive(
            "bassmanitram", "yacba", repo_path, branch="main"
        )

        print()
        print(f"{GREEN}✓{NC} Update complete!")

        if result.get("commit_info"):
            commit = result["commit_info"]
            print(f"  Version: {commit['short_sha']}")
            print(f"  Message: {commit['message']}")

        # Remove backup on success
        if backup and backup_path.exists():
            shutil.rmtree(backup_path)

        return True

    except UpdateError as e:
        print(f"{RED}✗{NC} Update failed: {e}", file=sys.stderr)

        # Restore backup if available
        if backup and backup_path.exists():
            print(f"{YELLOW}⚠{NC} Restoring from backup...", file=sys.stderr)
            if repo_path.exists():
                shutil.rmtree(repo_path)
            shutil.move(str(backup_path), str(repo_path))
            print(f"{GREEN}✓{NC} Restored from backup", file=sys.stderr)

        return False
    # Fix for lines 318-333
    except Exception as e:
        print(f"{RED}✗{NC} Unexpected error: {e}", file=sys.stderr)

        # Restore backup if available
        if backup and backup_path.exists():
            print(f"{YELLOW}⚠{NC} Restoring from backup...", file=sys.stderr)
            try:
                if repo_path.exists():
                    shutil.rmtree(repo_path)
                shutil.move(str(backup_path), str(repo_path))
                print(f"{GREEN}✓{NC} Restored from backup", file=sys.stderr)
            except Exception:
                print(f"{RED}✗{NC} Failed to restore backup", file=sys.stderr)
                print(f"  Backup is at: {backup_path}", file=sys.stderr)

        return False
        return False


def main():
    """Update YACBA from GitHub."""
    yacba_home = Path(os.environ.get("YACBA_HOME", Path.home() / ".yacba"))
    repo_path = yacba_home / "repo"

    if not repo_path.exists():
        print(
            f"{RED}✗{NC} YACBA code directory not found: {repo_path}", file=sys.stderr
        )
        print("Run 'yacba install' first.", file=sys.stderr)
        return 1

    print("YACBA Self-Update")
    print("=" * 50)
    print()

    # Check for updates
    print("Checking for updates...")
    update_info = check_for_updates(repo_path)

    if update_info["available"] is None:
        print(f"{YELLOW}⚠{NC} Could not check for updates (network error?)")
        print()
        response = input("Continue with update anyway? [y/N]: ").strip().lower()
        if response not in ["y", "yes"]:
            print("Cancelled.")
            return 0

    elif update_info["available"] is False:
        print(f"{GREEN}✓{NC} Already up to date!")

        if update_info["local_commit"]:
            commit = update_info["local_commit"]
            print(f"  Current: {commit['short_sha']} - {commit['message']}")

        print()
        print("To force update anyway:")
        print("  (Useful if files were modified or corrupted)")
        print()
        response = input("Force update? [y/N]: ").strip().lower()

        if response not in ["y", "yes"]:
            return 0

    else:
        print(f"{YELLOW}⚠{NC} Update available!")
        print()

        if update_info["local_commit"]:
            local = update_info["local_commit"]
            print(f"  Current:  {local['short_sha']} - {local['message']}")
        else:
            print("  Current:  Unknown version")

        if update_info["remote_commit"]:
            remote = update_info["remote_commit"]
            print(f"  Latest:   {remote['short_sha']} - {remote['message']}")

        print()

    # Perform update
    success = perform_update(repo_path, backup=True)

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
