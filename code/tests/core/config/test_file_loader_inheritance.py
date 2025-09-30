"""
Tests for ConfigProfile inheritance functionality.
"""

import pytest
from core.config.file_loader import ConfigProfile, ConfigFile


class TestConfigProfileInheritance:
    """Test profile inheritance scenarios."""

    def test_single_level_inheritance(self):
        """Test simple parent-child inheritance."""
        base = ConfigProfile(
            name="base",
            settings={"model": "gpt-4", "temperature": 0.5, "max_tokens": 2000}
        )
        
        dev = ConfigProfile(
            name="development",
            settings={"temperature": 0.7, "show_tool_use": True},
            inherits="base"
        )
        
        profiles = {"base": base, "development": dev}
        result = dev.resolve_inheritance(profiles)
        
        expected = {
            "model": "gpt-4",           # From base
            "temperature": 0.7,         # Overridden in dev
            "max_tokens": 2000,         # From base
            "show_tool_use": True       # Added in dev
        }
        assert result == expected

    def test_multi_level_inheritance(self):
        """Test inheritance chain: grandparent -> parent -> child."""
        grandparent = ConfigProfile(
            name="base",
            settings={"model": "gpt-4", "temperature": 0.5, "max_tokens": 2000}
        )
        
        parent = ConfigProfile(
            name="development",
            settings={"temperature": 0.7, "show_tool_use": True},
            inherits="base"
        )
        
        child = ConfigProfile(
            name="local_dev",
            settings={"max_tokens": 4000, "session": "dev-session"},
            inherits="development"
        )
        
        profiles = {
            "base": grandparent,
            "development": parent,
            "local_dev": child
        }
        
        result = child.resolve_inheritance(profiles)
        
        expected = {
            "model": "gpt-4",           # From grandparent
            "temperature": 0.7,         # From parent (overrode grandparent)
            "max_tokens": 4000,         # From child (overrode grandparent)
            "show_tool_use": True,      # From parent
            "session": "dev-session"    # From child
        }
        assert result == expected

    def test_missing_parent_profile(self):
        """Test inheritance from non-existent parent."""
        child = ConfigProfile(
            name="orphan",
            settings={"model": "claude-3", "temperature": 0.8},
            inherits="missing_parent"
        )
        
        profiles = {"orphan": child}
        
        # Should return only child settings when parent is missing
        result = child.resolve_inheritance(profiles)
        expected = {"model": "claude-3", "temperature": 0.8}
        assert result == expected

    def test_complex_override_patterns(self):
        """Test complex setting override patterns."""
        base = ConfigProfile(
            name="base",
            settings={
                "model": "gpt-4",
                "model_config": {"temperature": 0.5, "max_tokens": 2000},
                "tools": ["basic"],
                "features": {"logging": True, "caching": False}
            }
        )
        
        specialized = ConfigProfile(
            name="specialized",
            settings={
                "model_config": {"temperature": 0.7},  # Partial override
                "tools": ["advanced", "debug"],        # Complete override
                "features": {"caching": True}           # Partial override
            },
            inherits="base"
        )
        
        profiles = {"base": base, "specialized": specialized}
        result = specialized.resolve_inheritance(profiles)
        
        expected = {
            "model": "gpt-4",
            "model_config": {"temperature": 0.7},      # Completely replaced
            "tools": ["advanced", "debug"],            # Completely replaced
            "features": {"caching": True}               # Completely replaced
        }
        assert result == expected


class TestConfigFileWithInheritance:
    """Test ConfigFile with profile inheritance."""

    def test_config_file_inheritance_resolution(self):
        """Test that ConfigFile properly resolves inheritance."""
        base_profile = ConfigProfile(
            name="base",
            settings={"model": "gpt-4", "temperature": 0.5}
        )
        
        dev_profile = ConfigProfile(
            name="development", 
            settings={"show_tool_use": True, "temperature": 0.7},
            inherits="base"
        )
        
        config = ConfigFile(
            default_profile="development",
            profiles={"base": base_profile, "development": dev_profile},
            defaults={"max_files": 10}
        )
        
        result = config.get_profile_settings()
        
        expected = {
            "max_files": 10,            # From defaults
            "model": "gpt-4",           # From base profile
            "temperature": 0.7,         # From dev profile (overrode base)
            "show_tool_use": True       # From dev profile
        }
        assert result == expected

    def test_explicit_profile_selection(self):
        """Test selecting specific profile explicitly."""
        profiles = {
            "prod": ConfigProfile("prod", {"model": "gpt-4", "temperature": 0.2}),
            "dev": ConfigProfile("dev", {"model": "claude", "temperature": 0.8})
        }
        
        config = ConfigFile(
            default_profile="prod",
            profiles=profiles,
            defaults={"max_tokens": 1000}
        )
        
        # Test default profile
        default_result = config.get_profile_settings()
        assert default_result["model"] == "gpt-4"
        assert default_result["temperature"] == 0.2
        
        # Test explicit profile selection
        dev_result = config.get_profile_settings("dev")
        assert dev_result["model"] == "claude"
        assert dev_result["temperature"] == 0.8
        assert dev_result["max_tokens"] == 1000  # From defaults