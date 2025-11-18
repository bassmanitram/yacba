#!/usr/bin/env python3
"""
YACBA List Extras Subcommand

Show available model provider extras and tools.
"""

import sys
from extras_discovery import discover_all_extras


# ANSI color codes
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
BOLD = "\033[1m"
NC = "\033[0m"


# Descriptions for known extras
DESCRIPTIONS = {
    # Providers
    "anthropic": "Anthropic SDK (direct Claude API)",
    "openai": "OpenAI SDK (GPT models)",
    "litellm": "LiteLLM (100+ providers)",
    "ollama": "Ollama SDK (local models)",
    "gemini": "Google Gemini SDK",
    "mistralai": "Mistral AI SDK",
    "llamaapi": "Llama API SDK",
    "bedrock": "AWS Bedrock (extended support)",
    # Tools
    "tools": "Extended tool set",
    "a2a": "Agent-to-Agent communication",
}


def main():
    """List available extras."""
    print("YACBA Model Support")
    print("=" * 50)
    print()

    # Built-in support
    print("Built-in (always available, no installation needed):")
    print("  bedrock")
    print("      AWS Bedrock (all AWS models)")
    print("      Requires: AWS credentials configured")
    print()

    # Discover all extras
    all_extras = discover_all_extras()

    # Separate into categories
    tools = [e for e in all_extras if e.is_tool]
    providers = [e for e in all_extras if not e.is_tool]

    # Display providers
    if providers:
        print("Optional Extras (require installation):")
        print()
        print("Provider SDKs:")
        for extra in providers:
            status = f"{GREEN}INSTALLED{NC}" if extra.is_installed else "available"
            desc = DESCRIPTIONS.get(extra.name, "")

            print(f"  {extra.name:15} {desc:40} [{status}]")
        print()

    # Display tools
    if tools:
        print("Additional Capabilities:")
        for extra in tools:
            status = f"{GREEN}INSTALLED{NC}" if extra.is_installed else "available"
            desc = DESCRIPTIONS.get(extra.name, "")

            print(f"  {extra.name:15} {desc:40} [{status}]")
        print()

    # Installation instructions
    print("To install an extra:")
    print("  yacba install-extra <name>")
    print()
    print("Examples:")
    print("  yacba install-extra anthropic")
    print("  yacba install-extra litellm")
    print("  yacba install-extra tools")

    return 0


if __name__ == "__main__":
    sys.exit(main())
