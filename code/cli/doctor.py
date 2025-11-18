#!/usr/bin/env python3
"""
YACBA Doctor Subcommand

Health check and diagnostic information.
"""

import sys
import os
from pathlib import Path
from importlib import metadata
from extras_discovery import discover_all_extras


# ANSI color codes
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
BOLD = "\033[1m"
NC = "\033[0m"


# Descriptions for extras
EXTRA_DESCRIPTIONS = {
    # Providers
    "anthropic": "Anthropic SDK",
    "openai": "OpenAI SDK",
    "litellm": "LiteLLM",
    "ollama": "Ollama SDK",
    "gemini": "Google Gemini SDK",
    "mistralai": "Mistral AI SDK",
    "mistral": "Mistral AI SDK",
    "llamaapi": "Llama API SDK",
    "bedrock": "AWS Bedrock (extended)",
    "sagemaker": "AWS SageMaker",
    "writer": "Writer SDK",
    # Tools
    "tools": "Extended tool set",
    "a2a": "Agent-to-Agent",
}


def check_installation():
    """Check YACBA installation."""
    yacba_home = Path(os.environ.get("YACBA_HOME", Path.home() / ".yacba"))
    venv_path = yacba_home / ".venv"
    repo_path = yacba_home / "repo"

    return {
        "home": yacba_home,
        "home_exists": yacba_home.exists(),
        "venv": (venv_path / "bin" / "python3").exists(),
        "code": (repo_path / "code" / "yacba.py").exists(),
        "commit_info": (repo_path / ".commit_info").exists(),
    }


def get_package_version(package):
    """Get version of installed package."""
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return None


def check_yacba_package():
    """Check if YACBA itself is installed as package."""
    try:
        version = metadata.version("yacba")

        # Check if editable install
        dist = metadata.distribution("yacba")
        try:
            direct_url = dist.read_text("direct_url.json")
            is_editable = "editable" in direct_url.lower()
        except FileNotFoundError:
            is_editable = False

        return {
            "installed": True,
            "version": version,
            "editable": is_editable,
        }
    except metadata.PackageNotFoundError:
        return {"installed": False}


def main():
    """Run health check."""
    print("YACBA Health Check")
    print("=" * 50)
    print()

    # Check installation
    install_status = check_installation()

    if install_status["venv"]:
        py_version = sys.version.split()[0]
        print(f"{GREEN}✓{NC} Virtual environment: OK")
        print(f"  Python: {py_version}")
        print(f"  Location: {install_status['home']}")
    else:
        print(f"{RED}✗{NC} Virtual environment: MISSING")
        print(f"  Expected: {install_status['home']}/.venv")
        return 1
    print()

    # Check YACBA package
    print("YACBA Package:")
    pkg_status = check_yacba_package()
    if pkg_status["installed"]:
        mode = "editable" if pkg_status["editable"] else "regular"
        print(f"{GREEN}✓{NC} yacba ({pkg_status['version']}) - {mode} install")
    else:
        print(f"{YELLOW}⚠{NC} yacba package not installed")
        print(f"  Run: pip install -e {install_status['home']}/repo")

    # Check commit info
    if install_status["commit_info"]:
        print(f"{GREEN}✓{NC} Commit info available (.commit_info exists)")
    else:
        print(f"{YELLOW}⚠{NC} No commit info (installed via git or old version)")

    print()

    # Core packages
    print("Core Packages:")

    # YACBA core dependencies
    core_packages = {
        "strands-agent-factory": "Strands Agent Factory",
        "strands-agents": "Strands Agents SDK",
        "repl-toolkit": "REPL Toolkit",
        "profile-config": "Profile Config",
        "dataclass-args": "Dataclass Args",
    }

    all_ok = True
    for package, desc in core_packages.items():
        version = get_package_version(package)
        if version:
            print(f"{GREEN}✓{NC} {package} ({version})")
        else:
            print(f"{RED}✗{NC} {package} (not installed)")
            all_ok = False
    print()

    # Built-in frameworks
    print("Built-in Model Support:")
    boto3_version = get_package_version("boto3")
    if boto3_version:
        print(f"{GREEN}✓{NC} AWS Bedrock (boto3 {boto3_version})")
    else:
        print(f"{YELLOW}⚠{NC} AWS Bedrock (boto3 not installed)")
    print()

    # Optional extras (discovered from installed packages)
    print("Optional Extras:")
    all_extras = discover_all_extras()

    # Separate providers and tools
    providers = [e for e in all_extras if not e.is_tool]
    tools = [e for e in all_extras if e.is_tool]

    # Display providers
    if providers:
        for extra in providers:
            desc = EXTRA_DESCRIPTIONS.get(extra.name, extra.name.title())

            if extra.is_installed:
                # Try to get version from the actual installed package
                pkg_name = extra.name.replace("_", "-")
                version = get_package_version(pkg_name)
                if version:
                    print(f"  {GREEN}✓{NC} {extra.name} - {desc} ({version})")
                else:
                    print(f"  {GREEN}✓{NC} {extra.name} - {desc}")
            else:
                print(f"  {YELLOW}○{NC} {extra.name} - {desc} (not installed)")

    # Display tools
    if tools:
        for extra in tools:
            desc = EXTRA_DESCRIPTIONS.get(extra.name, extra.name.title())

            if extra.is_installed:
                print(f"  {GREEN}✓{NC} {extra.name} - {desc}")
            else:
                print(f"  {YELLOW}○{NC} {extra.name} - {desc} (not installed)")

    print()

    # Overall status
    if all_ok:
        print(f"Status: {GREEN}{BOLD}HEALTHY{NC}")
        print()
        print("To install optional providers:")
        print("  yacba install-extra anthropic")
        print("  yacba install-extra litellm")
        print()
        print("To see all available extras:")
        print("  yacba list-extras")
    else:
        print(f"Status: {RED}{BOLD}NEEDS ATTENTION{NC}")
        print()
        print("To fix core dependencies:")
        yacba_home = Path(os.environ.get("YACBA_HOME", Path.home() / ".yacba"))
        print(f"  {yacba_home}/.venv/bin/pip install -e {yacba_home}/repo")

    return 0


if __name__ == "__main__":
    sys.exit(main())
