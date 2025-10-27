#!/usr/bin/env python3
"""
Test script for the refactored YACBA using strands_agent_factory and repl_toolkit.

This script validates that all existing functionality continues to work
after the architectural refactoring.
"""

import sys
import asyncio
import subprocess
from pathlib import Path

# Add paths for the new dependencies
sys.path.insert(0, str(Path(__file__).parent.parent / "tmp" / "strands_agent_factory"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tmp" / "repl_toolkit"))

def run_test_command(cmd_args, input_text=None, timeout=10):
    """Run a YACBA command and return the result."""
    cmd = [sys.executable, "yacba_new.py"] + cmd_args
    
    try:
        result = subprocess.run(
            cmd, 
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path(__file__).parent
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "Timeout (expected for interactive mode)"
    except Exception as e:
        return 1, "", str(e)


def test_configuration_parsing():
    """Test that configuration parsing works correctly."""
    print("🧪 Testing configuration parsing...")
    
    # Test --show-config
    returncode, stdout, stderr = run_test_command(["--show-config"])
    
    if returncode == 0 and "model: litellm:gemini/gemini-2.5-flash" in stdout:
        print("  ✅ Configuration parsing works")
        return True
    else:
        print(f"  ❌ Configuration parsing failed: {returncode}, {stderr}")
        return False


def test_help_functionality():
    """Test that help functionality works."""
    print("🧪 Testing help functionality...")
    
    # Test --help
    returncode, stdout, stderr = run_test_command(["--help"])
    
    if returncode == 0 and "YACBA - Yet Another ChatBot Agent" in stdout:
        print("  ✅ Help functionality works")
        return True
    else:
        print(f"  ❌ Help functionality failed: {returncode}, {stderr}")
        return False


def test_headless_mode():
    """Test headless mode functionality."""
    print("🧪 Testing headless mode...")
    
    # Test headless mode with simple message
    returncode, stdout, stderr = run_test_command(
        ["--headless", "--initial-message", "Say hello"],
        timeout=15
    )
    
    # Check if response contains expected content
    if "Hello" in stdout or "hello" in stdout:
        print("  ✅ Headless mode works")
        return True
    else:
        print(f"  ❌ Headless mode failed: {returncode}")
        print(f"    stdout: {stdout[:200]}...")
        print(f"    stderr: {stderr[:200]}...")
        return False


def test_model_configuration():
    """Test model configuration options."""
    print("🧪 Testing model configuration...")
    
    # Test with different model
    returncode, stdout, stderr = run_test_command([
        "--model", "litellm:gemini/gemini-2.5-flash",
        "--show-config"
    ])
    
    if returncode == 0 and "gemini/gemini-2.5-flash" in stdout:
        print("  ✅ Model configuration works")
        return True
    else:
        print(f"  ❌ Model configuration failed: {returncode}, {stderr}")
        return False


def test_conversation_manager_options():
    """Test conversation manager configuration."""
    print("🧪 Testing conversation manager options...")
    
    # Test sliding window configuration
    returncode, stdout, stderr = run_test_command([
        "--conversation-manager", "sliding_window",
        "--window-size", "20",
        "--show-config"
    ])
    
    if returncode == 0 and "window_size: '20'" in stdout:
        print("  ✅ Conversation manager configuration works")
        return True
    else:
        print(f"  ❌ Conversation manager configuration failed: {returncode}, {stderr}")
        return False


def test_ui_customization():
    """Test UI customization options."""
    print("🧪 Testing UI customization...")
    
    # Test custom prompts
    returncode, stdout, stderr = run_test_command([
        "--cli-prompt", "<b>User:</b> ",
        "--response-prefix", "<b>Bot:</b> ",
        "--show-config"
    ])
    
    if returncode == 0 and "cli_prompt: <b>User:</b>" in stdout:
        print("  ✅ UI customization works")
        return True
    else:
        print(f"  ❌ UI customization failed: {returncode}, {stderr}")
        return False


def main():
    """Run all tests."""
    print("🚀 Testing Refactored YACBA")
    print("=" * 50)
    
    tests = [
        test_help_functionality,
        test_configuration_parsing,
        test_model_configuration,
        test_conversation_manager_options,
        test_ui_customization,
        test_headless_mode,  # This one last as it takes longer
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Refactored YACBA is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())