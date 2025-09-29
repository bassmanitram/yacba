# !/usr/bin/env python3
"""
Test script for model configuration functionality in YACBA.

This script tests various aspects of the model configuration system:
- JSON file loading
- Command-line overrides
- Property path parsing
- Type inference
- Error handling
"""

import sys
import json
import tempfile
from pathlib import Path

# Add the code directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from utils.model_config_parser import ModelConfigParser, parse_model_config, ModelConfigError
from core.config_parser import _create_model_config


def test_basic_parsing():
    """Test basic property override parsing."""
    print("🧪 Testing basic property override parsing...")

    parser = ModelConfigParser()

    test_cases = [
        ("temperature: 0.8", "temperature", 0.8),
        ("max_tokens: 2048", "max_tokens", 2048),
        ("stream: true", "stream", True),
        ("enabled: false", "enabled", False),
        ("model: null", "model", None),
        ("response_format.type: json_object", "response_format.type", "json_object"),
        ("safety_settings[0].threshold: BLOCK_LOW", "safety_settings[0].threshold", "BLOCK_LOW"),
    ]

    for override_str, expected_path, expected_value in test_cases:
        try:
            path, value = parser.parse_property_override(override_str)
            assert path == expected_path, f"Path mismatch: {path} != {expected_path}"
            assert value == expected_value, f"Value mismatch: {value} != {expected_value}"
            print(f"  ✅ {override_str} -> {path} = {value} ({type(value).__name__})")
        except Exception as e:
            print(f"  ❌ {override_str} failed: {e}")
            return False

    return True


def test_config_file_loading():
    """Test loading configuration from JSON files."""
    print("🧪 Testing configuration file loading...")

    # Test with existing sample file
    try:
        config = parse_model_config("sample-model-configs/openai-gpt4.json")
        print(f"  ✅ Loaded sample config: {len(config)} properties")

        # Verify some expected properties
        assert "temperature" in config, "Temperature not found in config"
        assert "max_tokens" in config, "max_tokens not found in config"
        assert isinstance(config["temperature"], (int, float)), "Temperature should be numeric"

    except Exception as e:
        print(f"  ❌ Failed to load sample config: {e}")
        return False

    # Test with temporary file
    try:
        temp_config = {
            "temperature": 0.9,
            "max_tokens": 1024,
            "response_format": {"type": "text"}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(temp_config, f)
            temp_file = f.name

        loaded_config = parse_model_config(temp_file)
        assert loaded_config == temp_config, "Loaded config doesn't match original"
        print("  ✅ Loaded temporary config file successfully")

        # Clean up
        Path(temp_file).unlink()

    except Exception as e:
        print(f"  ❌ Failed to load temporary config: {e}")
        return False

    return True


def test_config_merging():
    """Test merging configuration files with overrides."""
    print("🧪 Testing configuration merging...")

    try:
        overrides = [
            "temperature: 0.95",
            "max_tokens: 8192",
            "response_format.type: json_object",
            "new_property: test_value"
        ]

        merged_config = parse_model_config("sample-model-configs/openai-gpt4.json", overrides)

        # Verify overrides were applied
        assert merged_config["temperature"] == 0.95, "Temperature override not applied"
        assert merged_config["max_tokens"] == 8192, "max_tokens override not applied"
        assert merged_config["response_format"]["type"] == "json_object", "Nested override not applied"
        assert merged_config["new_property"] == "test_value", "New property not added"

        # Verify original properties are preserved
        assert "top_p" in merged_config, "Original property lost during merge"

        print(f"  ✅ Successfully merged config with {len(overrides)} overrides")

    except Exception as e:
        print(f"  ❌ Config merging failed: {e}")
        return False

    return True


def test_error_handling():
    """Test error handling for invalid configurations."""
    print("🧪 Testing error handling...")

    error_cases = [
        # Invalid file
        ("nonexistent-file.json", None, "file not found"),

        # Invalid override format
        (None, ["invalid_format"], "invalid format"),

        # Invalid array index
        (None, ["array[invalid]: value"], "invalid array index"),

        # Empty property path
        (None, [": value"], "empty property path"),
    ]

    for config_file, overrides, expected_error_type in error_cases:
        try:
            result = parse_model_config(config_file, overrides)
            print(f"  ❌ Expected error for {config_file}, {overrides} but got success")
            return False
        except ModelConfigError as e:
            print(f"  ✅ Correctly caught error for {expected_error_type}: {str(e)[: 50]}...")
        except Exception as e:
            print(f"  ⚠️  Unexpected error type for {expected_error_type}: {type(e).__name__}")

    return True


def test_integration_with_config_parser():
    """Test integration with the main config parser."""
    print("🧪 Testing integration with config parser...")

    try:
        # Test creating model config with file and overrides
        model_config = _create_model_config(
            "openai: gpt-4",
            "sample-model-configs/openai-gpt4.json",
            ["temperature: 0.85", "max_tokens: 3000"]
        )

        # Verify model config structure
        assert model_config.framework == "openai", "Framework not set correctly"
        assert model_config.model_id == "gpt-4", "Model ID not set correctly"
        assert model_config.get("temperature") == 0.85, "Temperature override not applied"
        assert model_config.get("max_tokens") == 3000, "max_tokens override not applied"

        print(f"  ✅ Integration test passed - created model config with {len(model_config)} properties")

    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        return False

    return True


def main():
    """Run all tests."""
    print("🚀 Running YACBA Model Configuration Tests")
    print("=" * 50)

    tests = [
        test_basic_parsing,
        test_config_file_loading,
        test_config_merging,
        test_error_handling,
        test_integration_with_config_parser,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ PASSED\n")
            else:
                failed += 1
                print("❌ FAILED\n")
        except Exception as e:
            failed += 1
            print(f"❌ FAILED with exception: {e}\n")

    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! Model configuration is working correctly.")
        return 0
    else:
        print("💥 Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
