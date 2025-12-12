"""
Comprehensive test for default value preservation across all configuration layers.

Tests both:
1. ARGUMENT_DEFAULTS preservation in YACBA
2. Profile defaults section preservation in profile-config
"""

import tempfile
import os
from pathlib import Path

import pytest

from config.factory import _resolve_profile_and_env
from config.arguments import ARGUMENT_DEFAULTS


class TestCompleteDefaultsPreservation:
    """Test complete configuration flow with all default layers."""

    def test_both_defaults_mechanisms_together(self):
        """
        Test that both ARGUMENT_DEFAULTS and profile defaults work together.
        
        This is the comprehensive test covering:
        - ARGUMENT_DEFAULTS (YACBA's code/config/arguments.py)
        - Profile defaults section (in config file)
        - Profile values (in config file)
        
        All three should be deep-merged correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config file matching user's actual config
            config_dir = Path(tmpdir) / ".yacba"
            config_dir.mkdir()
            config_file = config_dir / "config.yaml"
            
            config_file.write_text("""
defaults:
  repl:
    cli_prompt: "<b><ansigreen>You:</ansigreen></b> "
  agent:
    response_prefix: "<b><darkcyan>Chatbot:</darkcyan></b> "

profiles:
  default:
    agent:
      model: "custom-model"
""")
            
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Resolve profile using YACBA's actual function
                result = _resolve_profile_and_env("default")
                
                print(f"\nResolved config: {result}")
                
                # Verify all three layers are present:
                
                # 1. From ARGUMENT_DEFAULTS (YACBA layer)
                assert "agent" in result
                assert "agent_id" in result["agent"], \
                    f"agent_id missing (from ARGUMENT_DEFAULTS). Got: {result.get('agent', {})}"
                assert result["agent"]["agent_id"] == "yacba_agent", \
                    f"Expected agent_id='yacba_agent' from ARGUMENT_DEFAULTS, got '{result['agent']['agent_id']}'"
                
                # 2. From profile defaults section (profile-config layer)
                assert "response_prefix" in result["agent"], \
                    f"response_prefix missing (from profile defaults). Got: {result.get('agent', {})}"
                assert result["agent"]["response_prefix"] == "<b><darkcyan>Chatbot:</darkcyan></b> ", \
                    f"Expected response_prefix from defaults, got '{result['agent'].get('response_prefix')}'"
                
                assert "repl" in result
                assert "cli_prompt" in result["repl"], \
                    f"cli_prompt missing (from profile defaults). Got: {result.get('repl', {})}"
                assert result["repl"]["cli_prompt"] == "<b><ansigreen>You:</ansigreen></b> ", \
                    f"Expected cli_prompt from defaults, got '{result['repl'].get('cli_prompt')}'"
                
                # 3. From profile section
                assert result["agent"]["model"] == "custom-model", \
                    f"Expected model from profile, got '{result['agent'].get('model')}'"
                
                print("\n✅ ALL CHECKS PASSED:")
                print(f"  ✓ agent_id from ARGUMENT_DEFAULTS: {result['agent']['agent_id']}")
                print(f"  ✓ response_prefix from profile defaults: {result['agent']['response_prefix'][:20]}...")
                print(f"  ✓ cli_prompt from profile defaults: {result['repl']['cli_prompt'][:20]}...")
                print(f"  ✓ model from profile: {result['agent']['model']}")
                
            finally:
                os.chdir(original_cwd)

    def test_complex_nested_defaults_merge(self):
        """Test complex scenario with multiple nested levels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".yacba"
            config_dir.mkdir()
            config_file = config_dir / "config.yaml"
            
            config_file.write_text("""
defaults:
  agent:
    conversation_manager_type: "sliding_window"
    sliding_window_size: 40
    response_prefix: "AI: "
    model_config:
      temperature: 0.7
  repl:
    max_files: 100

profiles:
  default:
    agent:
      model: "gpt-4"
      model_config:
        max_tokens: 2000
""")
            
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                result = _resolve_profile_and_env("default")
                
                # Check all layers are preserved
                agent = result["agent"]
                
                # From ARGUMENT_DEFAULTS
                assert agent.get("agent_id") == "yacba_agent"
                
                # From profile defaults
                assert agent.get("conversation_manager_type") == "sliding_window"
                assert agent.get("sliding_window_size") == 40
                assert agent.get("response_prefix") == "AI: "
                
                # From profile defaults + profile (model_config should deep merge)
                model_config = agent.get("model_config", {})
                assert model_config.get("temperature") == 0.7  # From defaults
                assert model_config.get("max_tokens") == 2000  # From profile
                
                # From profile
                assert agent.get("model") == "gpt-4"
                
                # From ARGUMENT_DEFAULTS (repl section)
                repl = result["repl"]
                assert repl.get("headless") == False
                assert repl.get("cli_prompt") is None
                assert repl.get("max_files") == 100  # From profile defaults (overrides ARGUMENT_DEFAULTS)
                
                print("\n✅ Complex nested merge works correctly!")
                
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
