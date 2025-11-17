#!/usr/bin/env python3
"""
YACBA List Extras Subcommand

Display available model provider extras and their installation status.
"""

import sys
import re
from pathlib import Path
from importlib import metadata


# ANSI color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
NC = '\033[0m'


def discover_extras():
    """Discover available extras from strands-agents metadata."""
    try:
        meta = metadata.metadata('strands-agents')
        
        # Get built-in (required dependencies without "extra ==")
        builtin = []
        extras = []
        
        for line in str(meta).split('\n'):
            if line.startswith('Requires-Dist:'):
                if 'extra ==' not in line and 'boto3' in line:
                    builtin.append('bedrock')
            elif line.startswith('Provides-Extra:'):
                extra = line.split(':', 1)[1].strip()
                if extra not in ['all', 'dev', 'docs', 'otel']:
                    extras.append(extra)
        
        return sorted(set(builtin)), sorted(set(extras))
    
    except Exception as e:
        print(f"Error discovering extras: {e}", file=sys.stderr)
        return [], []


def check_extra_installed(extra):
    """Check if an extra is installed."""
    package_map = {
        'anthropic': 'anthropic',
        'openai': 'openai',
        'gemini': 'google-generativeai',
        'litellm': 'litellm',
        'ollama': 'ollama',
        'mistral': 'mistralai',
        'llamaapi': 'llama-api-client',
        'writer': 'writer-sdk',
        'sagemaker': 'boto3-stubs',
        'a2a': 'a2a-sdk',
    }
    
    package = package_map.get(extra, extra)
    
    try:
        metadata.version(package)
        return True
    except metadata.PackageNotFoundError:
        return False


def get_extra_description(extra):
    """Get human-readable description for an extra."""
    descriptions = {
        'anthropic': 'Anthropic SDK (direct Claude API)',
        'openai': 'OpenAI SDK (direct GPT API)',
        'gemini': 'Google Gemini SDK',
        'litellm': 'LiteLLM (100+ providers)',
        'ollama': 'Ollama Python SDK',
        'mistral': 'Mistral AI SDK',
        'llamaapi': 'Llama API SDK',
        'writer': 'Writer AI SDK',
        'sagemaker': 'AWS SageMaker SDK',
        'a2a': 'Agent-to-Agent tools',
        'bedrock': 'AWS Bedrock (all AWS models)',
    }
    return descriptions.get(extra, extra)


def main():
    """List available extras and their status."""
    print("YACBA Model Support")
    print("=" * 50)
    print()
    
    builtin, extras = discover_extras()
    
    # Show built-in
    if builtin:
        print("Built-in (always available, no installation needed):")
        for framework in builtin:
            desc = get_extra_description(framework)
            print(f"  {framework}")
            print(f"      {GREEN}✓{NC} {desc}")
            if framework == 'bedrock':
                print(f"      Requires: AWS credentials configured")
        print()
    
    # Show optional extras
    if extras:
        print("Optional Extras (require installation):")
        print()
        
        # Categorize
        providers = [e for e in extras if e != 'a2a']
        tools = [e for e in extras if e == 'a2a']
        
        if providers:
            print("Provider SDKs:")
            for provider in providers:
                desc = get_extra_description(provider)
                status = f"[{GREEN}INSTALLED{NC}]" if check_extra_installed(provider) else ""
                print(f"  {provider:15} {desc:40} {status}")
            print()
        
        if tools:
            print("Tools:")
            for tool in tools:
                desc = get_extra_description(tool)
                status = f"[{GREEN}INSTALLED{NC}]" if check_extra_installed(tool) else ""
                print(f"  {tool:15} {desc:40} {status}")
            print()
    
    print("Install: yacba install-extra <name> [<name2> ...]")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
