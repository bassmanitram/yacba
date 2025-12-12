"""
Tests for agent_id default value preservation with ARGUMENT_DEFAULTS.

This test verifies that ARGUMENT_DEFAULTS in code/config/arguments.py
properly overrides nested dataclass defaults when profiles are used.
"""

import tempfile
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from config.factory import _resolve_profile_and_env
from config.arguments import ARGUMENT_DEFAULTS


class TestAgentIdDefaultPreservation:
    """Test that agent_id default from ARGUMENT_DEFAULTS is preserved."""

    def test_argument_defaults_has_agent_id(self):
        """Verify ARGUMENT_DEFAULTS contains agent_id override."""
        assert "agent" in ARGUMENT_DEFAULTS
        assert "agent_id" in ARGUMENT_DEFAULTS["agent"]
        assert ARGUMENT_DEFAULTS["agent"]["agent_id"] == "yacba_agent"

    def test_resolve_profile_no_config_file(self):
        """Test that agent_id is preserved when no config file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory where no config exists
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Should use ARGUMENT_DEFAULTS when no config file
                result = _resolve_profile_and_env("default")
                
                assert isinstance(result, dict)
                assert "agent" in result
                assert "agent_id" in result["agent"]
                assert result["agent"]["agent_id"] == "yacba_agent"
                
            finally:
                os.chdir(original_cwd)

    def test_resolve_profile_with_partial_config_file(self):
        """Test that agent_id is preserved when config file doesn't specify it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config file that only sets model, not agent_id
            config_dir = Path(tmpdir) / ".yacba"
            config_dir.mkdir()
            config_file = config_dir / "config.yaml"
            
            config_file.write_text("""
profiles:
  default:
    agent:
      model: "custom-model"
""")
            
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Resolve profile
                result = _resolve_profile_and_env("default")
                
                # Should have model from profile AND agent_id from ARGUMENT_DEFAULTS
                assert isinstance(result, dict)
                assert "agent" in result
                
                # This is the key test - agent_id should be from ARGUMENT_DEFAULTS
                assert "agent_id" in result["agent"], f"agent_id missing from result: {result}"
                assert result["agent"]["agent_id"] == "yacba_agent", \
                    f"Expected agent_id='yacba_agent', got '{result['agent']['agent_id']}'"
                
                # Model should be from profile
                assert result["agent"]["model"] == "custom-model"
                
            finally:
                os.chdir(original_cwd)

    def test_resolve_profile_explicit_override(self):
        """Test that explicit agent_id in profile overrides ARGUMENT_DEFAULTS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config file that explicitly sets agent_id
            config_dir = Path(tmpdir) / ".yacba"
            config_dir.mkdir()
            config_file = config_dir / "config.yaml"
            
            config_file.write_text("""
profiles:
  default:
    agent:
      model: "custom-model"
      agent_id: "explicit-agent"
""")
            
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Resolve profile
                result = _resolve_profile_and_env("default")
                
                # Explicit agent_id should override ARGUMENT_DEFAULTS
                assert result["agent"]["agent_id"] == "explicit-agent"
                assert result["agent"]["model"] == "custom-model"
                
            finally:
                os.chdir(original_cwd)

    def test_resolve_profile_env_var_override(self):
        """Test that env var overrides both ARGUMENT_DEFAULTS and profile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config file
            config_dir = Path(tmpdir) / ".yacba"
            config_dir.mkdir()
            config_file = config_dir / "config.yaml"
            
            config_file.write_text("""
profiles:
  default:
    agent:
      model: "custom-model"
      agent_id: "profile-agent"
""")
            
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Mock env var
                with patch.dict(os.environ, {"YACBA_AGENT_AGENT_ID": "env-agent"}):
                    # Need to reload arguments.py to pick up env var
                    from config import arguments
                    import importlib
                    importlib.reload(arguments)
                    
                    # Resolve profile
                    result = _resolve_profile_and_env("default")
                    
                    # Env var should win
                    assert result["agent"]["agent_id"] == "env-agent"
                    
            finally:
                os.chdir(original_cwd)

    def test_resolve_profile_multiple_nested_sections(self):
        """Test that both agent and repl defaults are preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config file that only sets agent.model
            config_dir = Path(tmpdir) / ".yacba"
            config_dir.mkdir()
            config_file = config_dir / "config.yaml"
            
            config_file.write_text("""
profiles:
  default:
    agent:
      model: "custom-model"
""")
            
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Resolve profile
                result = _resolve_profile_and_env("default")
                
                # Should have agent.agent_id from ARGUMENT_DEFAULTS
                assert result["agent"]["agent_id"] == "yacba_agent"
                
                # Should have repl section from ARGUMENT_DEFAULTS
                assert "repl" in result
                assert result["repl"]["headless"] == False
                assert result["repl"]["max_files"] == 20
                
                # And agent.model from profile
                assert result["agent"]["model"] == "custom-model"
                
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
