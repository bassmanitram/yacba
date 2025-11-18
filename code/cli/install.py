#!/usr/bin/env python3
"""
YACBA Install Subcommand

Interactive installation of model provider extras and configuration.
"""

import sys
import argparse
from pathlib import Path


def main():
    """Interactive installation wizard."""
    parser = argparse.ArgumentParser(description="YACBA installation wizard")
    parser.add_argument(
        "--interactive", action="store_true", help="Run interactive setup"
    )
    args = parser.parse_args()

    if not args.interactive:
        print("Run with --interactive for guided setup")
        return 0

    print("YACBA Installation Wizard")
    print("=" * 50)
    print()

    # TODO: Implement interactive setup
    # - Ask about model providers
    # - Install extras
    # - Configure default model
    # - Set up initial config file

    print("✓ Base installation complete")
    print()
    print("To install model providers:")
    print("  yacba install-extra anthropic")
    print("  yacba install-extra litellm")
    print()
    print("To see all available providers:")
    print("  yacba list-extras")

    return 0


if __name__ == "__main__":
    sys.exit(main())
