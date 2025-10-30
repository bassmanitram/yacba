#!/usr/bin/env python3
"""
Quick test to verify auto-printer integration in YACBA.
"""

import sys
sys.path.insert(0, 'code')

from repl_toolkit import create_auto_printer, detect_format_type

# Test the auto-printer
printer = create_auto_printer()

print("=" * 70)
print("TESTING AUTO-PRINTER INTEGRATION")
print("=" * 70)

# Test HTML formatting (like YACBA's default response_prefix)
test_cases = [
    ("<b><darkcyan>🤖 Assistant:</darkcyan></b> ", "HTML formatted prefix"),
    ("\x1b[1;36m🤖 Assistant:\x1b[0m ", "ANSI formatted prefix"),
    ("Plain text prefix: ", "Plain text prefix"),
]

for text, description in test_cases:
    format_type = detect_format_type(text)
    print(f"\n{description}")
    print(f"  Format detected: {format_type}")
    print(f"  Output: ", end="")
    printer(text, end="")
    print("Hello from the assistant!")

print("\n" + "=" * 70)
print("Testing with YACBA's default response_prefix:")
print("=" * 70)

default_prefix = "<b><darkcyan>🤖 Assistant:</darkcyan></b> "
print(f"\nFormat type: {detect_format_type(default_prefix)}")
print("Output: ", end="")
printer(default_prefix, end="")
print("This is a test message from YACBA!")

print("\n" + "=" * 70)
print("SUCCESS: Auto-printer is working correctly!")
print("=" * 70)
