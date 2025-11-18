#!/usr/bin/env python3
"""
GitHub Archive Downloader

Download and extract GitHub repository archives without git.
"""

import sys
import urllib.request
import tarfile
import shutil
import json
from pathlib import Path
from typing import Optional, Dict, Any


class DownloadError(Exception):
    """Download operation failed."""
    pass


def get_latest_commit_info(repo_owner: str, repo_name: str, branch: str = "main") -> Optional[Dict[str, Any]]:
    """
    Get latest commit information from GitHub API.
    
    Args:
        repo_owner: Repository owner (e.g., 'bassmanitram')
        repo_name: Repository name (e.g., 'yacba')
        branch: Branch name (default: 'main')
    
    Returns:
        Dict with commit info (sha, message, date) or None if failed
    """
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{branch}"
    
    try:
        req = urllib.request.Request(api_url)
        req.add_header('Accept', 'application/vnd.github.v3+json')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            return {
                'sha': data['sha'],
                'short_sha': data['sha'][:7],
                'message': data['commit']['message'].split('\n')[0],
                'date': data['commit']['committer']['date'],
                'author': data['commit']['author']['name'],
            }
    except Exception as e:
        print(f"Warning: Could not fetch commit info: {e}", file=sys.stderr)
        return None


def download_with_progress(url: str, dest_path: Path, show_progress: bool = True) -> None:
    """
    Download file with progress indicator.
    
    Args:
        url: URL to download
        dest_path: Destination file path
        show_progress: Whether to show progress bar
    
    Raises:
        DownloadError: If download fails
    """
    try:
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/vnd.github.v3+json')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(dest_path, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    
                    downloaded += len(chunk)
                    f.write(chunk)
                    
                    if show_progress and total_size > 0:
                        percent = (downloaded / total_size) * 100
                        mb_downloaded = downloaded / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024)
                        print(f"\rDownloading: {mb_downloaded:.1f}/{mb_total:.1f} MB ({percent:.0f}%)", end='', flush=True)
            
            if show_progress:
                print()  # New line after progress
                
    except Exception as e:
        raise DownloadError(f"Download failed: {e}")


def extract_tarball(tar_path: Path, extract_to: Path, strip_components: int = 1) -> Path:
    """
    Extract tarball, optionally stripping top-level directory.
    
    Args:
        tar_path: Path to .tar.gz file
        extract_to: Directory to extract into
        strip_components: Number of leading path components to strip
    
    Returns:
        Path to extracted content
    
    Raises:
        DownloadError: If extraction fails
    """
    try:
        extract_to.mkdir(parents=True, exist_ok=True)
        
        with tarfile.open(tar_path, 'r:gz') as tar:
            # Get all members
            members = tar.getmembers()
            
            if strip_components > 0:
                # Strip leading path components
                for member in members:
                    parts = Path(member.name).parts
                    if len(parts) > strip_components:
                        member.name = str(Path(*parts[strip_components:]))
                        tar.extract(member, extract_to)
            else:
                tar.extractall(extract_to)
        
        return extract_to
        
    except Exception as e:
        raise DownloadError(f"Extraction failed: {e}")


def download_github_archive(
    repo_owner: str,
    repo_name: str,
    target_dir: Path,
    branch: str = "main",
    show_progress: bool = True
) -> Dict[str, Any]:
    """
    Download and extract GitHub repository archive.
    
    Args:
        repo_owner: Repository owner
        repo_name: Repository name
        target_dir: Target directory for extracted content
        branch: Branch to download
        show_progress: Show progress indicators
    
    Returns:
        Dict with download info (commit sha, etc.)
    
    Raises:
        DownloadError: If download or extraction fails
    """
    # GitHub archive URL
    archive_url = f"https://github.com/{repo_owner}/{repo_name}/archive/refs/heads/{branch}.tar.gz"
    
    # Temporary download location
    temp_dir = Path("/tmp") / f"yacba-download-{repo_name}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_tar = temp_dir / f"{repo_name}.tar.gz"
    
    try:
        # Get commit info before download
        if show_progress:
            print(f"Fetching latest commit info...")
        commit_info = get_latest_commit_info(repo_owner, repo_name, branch)
        
        # Download
        if show_progress:
            print(f"Downloading from {archive_url}...")
        download_with_progress(archive_url, temp_tar, show_progress)
        
        # Extract
        if show_progress:
            print(f"Extracting to {target_dir}...")
        
        # Remove target if exists
        if target_dir.exists():
            shutil.rmtree(target_dir)
        
        extract_tarball(temp_tar, target_dir, strip_components=1)
        
        # Save commit info
        if commit_info:
            commit_file = target_dir / ".commit_info"
            with open(commit_file, 'w') as f:
                json.dump(commit_info, f, indent=2)
        
        if show_progress:
            print(f"✓ Successfully downloaded to {target_dir}")
            if commit_info:
                print(f"  Commit: {commit_info['short_sha']} - {commit_info['message']}")
        
        return {
            'success': True,
            'target_dir': target_dir,
            'commit_info': commit_info,
        }
        
    except DownloadError:
        raise
    except Exception as e:
        raise DownloadError(f"Download failed: {e}")
    finally:
        # Cleanup temp files
        if temp_tar.exists():
            temp_tar.unlink()
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
            except:
                pass


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
        with open(commit_file, 'r') as f:
            return json.load(f)
    except:
        return None


if __name__ == "__main__":
    # Simple test
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    else:
        target = Path("/tmp/yacba-test")
    
    print(f"Testing download to {target}")
    result = download_github_archive("bassmanitram", "yacba", target)
    print(f"Result: {result}")
