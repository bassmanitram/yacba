#!/usr/bin/env python3
"""
YACBA Doctor Subcommand

Health check and diagnostic information.
"""

import sys
import os
from pathlib import Path
from importlib import metadata


# ANSI color codes
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BOLD = '\033[1m'
NC = '\033[0m'


def check_installation():
    """Check YACBA installation."""
    yacba_home = Path(os.environ.get('YACBA_HOME', Path.home() / ".yacba"))
    venv_path = yacba_home / ".venv"
    code_path = yacba_home / "code"
    
    return {
        'home': yacba_home,
        'home_exists': yacba_home.exists(),
        'venv': (venv_path / "bin" / "python3").exists(),
        'code': (code_path / "yacba.py").exists(),
    }


def get_package_version(package):
    """Get version of installed package."""
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return None


def main():
    """Run health check."""
    print("YACBA Health Check")
    print("=" * 50)
    print()
    
    # Check installation
    install_status = check_installation()
    
    if install_status['venv']:
        py_version = sys.version.split()[0]
        print(f"{GREEN}✓{NC} Virtual environment: OK")
        print(f"  Python: {py_version}")
        print(f"  Location: {install_status['home']}")
    else:
        print(f"{RED}✗{NC} Virtual environment: MISSING")
        print(f"  Expected: {install_status['home']}/.venv")
        return 1
    print()
    
    # Core packages
    print("Core Packages:")
    
    # YACBA core dependencies
    core_packages = {
        'strands-agent-factory': 'Strands Agent Factory',
        'strands-agents': 'Strands Agents SDK',
        'repl-toolkit': 'REPL Toolkit',
        'profile-config': 'Profile Config',
    }
    
    all_ok = True
    for package, desc in core_packages.items():
        version = get_package_version(package)
        if version:
            print(f"{GREEN}✓{NC} {package} ({version}) - {desc}")
        else:
            print(f"{RED}✗{NC} {package} (not installed) - {desc}")
            all_ok = False
    print()
    
    # Built-in frameworks
    print("Built-in Model Support:")
    boto3_version = get_package_version('boto3')
    if boto3_version:
        print(f"{GREEN}✓{NC} bedrock - AWS Bedrock (boto3 {boto3_version})")
    else:
        print(f"{RED}✗{NC} bedrock - AWS Bedrock (boto3 missing)")
    print()
    
    # Optional extras
    print("Optional Extras:")
    extras = {
        'anthropic': 'Anthropic SDK',
        'openai': 'OpenAI SDK',
        'google-generativeai': 'Google Gemini SDK',
        'litellm': 'LiteLLM',
        'ollama': 'Ollama SDK',
        'mistralai': 'Mistral AI SDK',
    }
    
    for extra, desc in extras.items():
        version = get_package_version(extra)
        if version:
            print(f"{GREEN}✓{NC} [{extra}] - {desc} ({version})")
        else:
            print(f"  {YELLOW}✗{NC} [{extra}] - {desc} (not installed)")
    print()
    
    # Overall status
    if all_ok and boto3_version:
        print(f"Installation: {GREEN}{BOLD}HEALTHY{NC}")
    else:
        print(f"Installation: {RED}{BOLD}NEEDS ATTENTION{NC}")
        if not all_ok:
            print()
            print("To fix core dependencies:")
            yacba_home = Path(os.environ.get('YACBA_HOME', Path.home() / ".yacba"))
            print(f"  {yacba_home}/.venv/bin/pip install -r {yacba_home}/code/requirements.txt")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
