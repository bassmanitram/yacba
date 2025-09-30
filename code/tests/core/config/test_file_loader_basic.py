"""Basic tests for file_loader module."""

import pytest
from core.config.file_loader import ConfigProfile, ConfigFile

def test_config_profile_basic():
    """Test basic ConfigProfile functionality."""
    profile = ConfigProfile(name="test", settings={"model": "gpt-4"})
    assert profile.name == "test"
    assert profile.settings["model"] == "gpt-4"

def test_config_file_basic():
    """Test basic ConfigFile functionality."""
    config = ConfigFile(defaults={"temp": 0.5})
    result = config.get_profile_settings()
    assert result == {"temp": 0.5}