#!/usr/bin/env python3
"""
YACBA Extras Discovery Module

Centralized logic for discovering available extras from strands packages.
"""

from importlib import metadata
from typing import Dict, List, Tuple
from dataclasses import dataclass


# Extras to skip (meta-extras, non-provider/non-tool)
SKIP_EXTRAS = {'all', 'dev', 'docs', 'otel', 'all-providers', 'all-tools', 'full'}

# Extras that are tools/capabilities, not providers
TOOL_EXTRAS = {'tools', 'a2a'}


@dataclass
class ExtraInfo:
    """Information about an installable extra."""
    name: str
    package: str  # 'strands-agent-factory' or 'strands-agents'
    is_tool: bool
    is_installed: bool = False
    description: str = ""


def get_package_extras(package_name: str) -> List[str]:
    """Get all extras provided by a package."""
    try:
        meta = metadata.metadata(package_name)
        extras = []
        for line in str(meta).split('\n'):
            if line.startswith('Provides-Extra:'):
                extra = line.split(':', 1)[1].strip()
                if extra not in SKIP_EXTRAS:
                    extras.append(extra)
        return extras
    except metadata.PackageNotFoundError:
        return []


def is_extra_installed(extra_name: str) -> bool:
    """Check if an extra's dependencies are installed."""
    # Map common extras to their key packages
    extra_packages = {
        'anthropic': 'anthropic',
        'openai': 'openai',
        'litellm': 'litellm',
        'ollama': 'ollama',
        'bedrock': 'boto3',
        'gemini': 'google-generativeai',
        'mistralai': 'mistralai',
        'llamaapi': 'llamaapi',
        'tools': 'strands-agents-tools',
        'a2a': 'strands-agents-tools',
    }
    
    check_package = extra_packages.get(extra_name)
    if not check_package:
        return False
    
    try:
        metadata.version(check_package)
        return True
    except metadata.PackageNotFoundError:
        return False


def discover_all_extras() -> List[ExtraInfo]:
    """
    Discover all available extras from strands packages.
    
    Priority:
    1. Extras from strands-agent-factory (complete integrations)
    2. Extras from strands-agents only (framework-only support)
    
    Returns:
        List of ExtraInfo objects sorted by category and name
    """
    # Get extras from both packages
    factory_extras = set(get_package_extras('strands-agent-factory'))
    agents_extras = set(get_package_extras('strands-agents'))
    
    results = []
    
    # Add factory extras (these take priority)
    for extra in sorted(factory_extras):
        results.append(ExtraInfo(
            name=extra,
            package='strands-agent-factory',
            is_tool=(extra in TOOL_EXTRAS),
            is_installed=is_extra_installed(extra)
        ))
    
    # Add agents-only extras (not in factory)
    agents_only = agents_extras - factory_extras
    for extra in sorted(agents_only):
        results.append(ExtraInfo(
            name=extra,
            package='strands-agents',
            is_tool=(extra in TOOL_EXTRAS),
            is_installed=is_extra_installed(extra)
        ))
    
    # Sort: tools first, then providers (alphabetically within each)
    results.sort(key=lambda x: (not x.is_tool, x.name))
    
    return results


def get_extra_info(extra_name: str) -> ExtraInfo:
    """Get info for a specific extra."""
    all_extras = discover_all_extras()
    for extra in all_extras:
        if extra.name == extra_name:
            return extra
    
    # Not found - return a default
    return ExtraInfo(
        name=extra_name,
        package='strands-agents',  # fallback
        is_tool=False,
        is_installed=False
    )


def get_install_command(extra_name: str) -> Tuple[str, List[str]]:
    """
    Get the pip install command for an extra.
    
    Returns:
        Tuple of (package_spec, pip_args)
        e.g., ('strands-agent-factory[anthropic]', ['-U'])
    """
    extra_info = get_extra_info(extra_name)
    package_spec = f"{extra_info.package}[{extra_name}]"
    return package_spec, ['-U']  # Always upgrade


if __name__ == "__main__":
    # Test discovery
    print("Discovered Extras:")
    for extra in discover_all_extras():
        status = "INSTALLED" if extra.is_installed else "available"
        category = "tool" if extra.is_tool else "provider"
        print(f"  {extra.name:20} [{category:8}] from {extra.package:30} [{status}]")
