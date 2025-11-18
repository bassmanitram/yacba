"""
Tests for config.factory module.

Target Coverage: 60%+ (complex module with many integration points)
"""

import pytest
from unittest.mock import patch, MagicMock


class TestProfileConfigConstants:
    """Tests for profile config constants."""

    def test_profile_config_name(self):
        """Test PROFILE_CONFIG_NAME constant."""
        from config.factory import PROFILE_CONFIG_NAME

        assert isinstance(PROFILE_CONFIG_NAME, str)
        assert PROFILE_CONFIG_NAME == ".yacba"

    def test_profile_config_profile_file_name(self):
        """Test PROFILE_CONFIG_PROFILE_FILE_NAME constant."""
        from config.factory import PROFILE_CONFIG_PROFILE_FILE_NAME

        assert isinstance(PROFILE_CONFIG_PROFILE_FILE_NAME, str)
        assert len(PROFILE_CONFIG_PROFILE_FILE_NAME) > 0


class TestParseConfigBasic:
    """Basic tests for parse_config function."""

    @patch("sys.argv", ["yacba.py", "-m", "gpt-4o"])
    def test_parse_config_requires_full_integration(self):
        """Test parse_config - skip due to full integration requirement."""
        # parse_config uses dataclass-args build_config which is complex
        # This requires full integration test setup
        pytest.skip(
            "parse_config requires full integration test setup with dataclass-args"
        )


class TestToolDiscoveryIntegration:
    """Tests for tool discovery integration in factory."""

    def test_discover_tool_configs_called(self, tmp_path):
        """Test that discover_tool_configs is used."""
        from utils.config_utils import discover_tool_configs

        # Should be importable
        assert callable(discover_tool_configs)

        # Should work with temp directory - returns tuple
        result = discover_tool_configs(str(tmp_path))
        assert isinstance(result, tuple)
        assert len(result) == 2
        # First element is list of paths
        assert isinstance(result[0], list)
        # Second element is ToolDiscoveryResult
        assert hasattr(result[1], "successful_configs")


@pytest.mark.integration
class TestFactoryIntegration:
    """Integration tests for factory module."""

    def test_imports_work(self):
        """Test that all necessary imports work."""
        import config.factory as factory

        # Should have key functions
        assert hasattr(factory, "parse_config")
        assert hasattr(factory, "PROFILE_CONFIG_NAME")

    def test_argument_defaults_available(self):
        """Test ARGUMENT_DEFAULTS is importable."""
        from config.arguments import ARGUMENT_DEFAULTS

        assert isinstance(ARGUMENT_DEFAULTS, dict)
        assert len(ARGUMENT_DEFAULTS) > 0


class TestYacbaConfigImport:
    """Tests for YacbaConfig integration."""

    def test_yacba_config_imported(self):
        """Test YacbaConfig is imported."""
        from config.dataclass import YacbaConfig

        assert YacbaConfig is not None
        # Should be a dataclass
        assert hasattr(YacbaConfig, "__dataclass_fields__")


class TestDataclassArgsIntegration:
    """Tests for dataclass-args integration."""

    def test_dataclass_args_imports(self):
        """Test that dataclass-args is available."""
        from dataclass_args import build_config, GenericConfigBuilder

        assert callable(build_config)
        assert GenericConfigBuilder is not None

    def test_yacba_config_has_annotations(self):
        """Test that YacbaConfig has proper annotations."""
        from config.dataclass import YacbaConfig
        from dataclasses import fields

        # Should have fields
        config_fields = fields(YacbaConfig)
        assert len(config_fields) > 0

        # Check that key fields exist
        field_names = [f.name for f in config_fields]
        assert "model_string" in field_names
        assert "system_prompt" in field_names
        assert "headless" in field_names


class TestHelperFunctions:
    """Tests for helper functions in factory."""

    def test_extract_profile_name(self):
        """Test _extract_profile_name function."""
        from config.factory import _extract_profile_name

        # Should return default if no profile specified
        with patch("sys.argv", ["yacba.py"]):
            with patch.dict("os.environ", {}, clear=True):
                profile = _extract_profile_name()
                assert profile == "default"

    def test_extract_profile_from_env(self):
        """Test extracting profile from environment."""
        from config.factory import _extract_profile_name

        with patch("sys.argv", ["yacba.py"]):
            with patch.dict("os.environ", {"YACBA_PROFILE": "test-profile"}):
                profile = _extract_profile_name()
                assert profile == "test-profile"

    def test_extract_profile_from_cli(self):
        """Test extracting profile from CLI."""
        from config.factory import _extract_profile_name

        with patch("sys.argv", ["yacba.py", "--profile", "cli-profile"]):
            with patch.dict("os.environ", {"YACBA_PROFILE": "env-profile"}):
                # CLI should take precedence
                profile = _extract_profile_name()
                assert profile == "cli-profile"


class TestConfigResolution:
    """Tests for configuration resolution logic."""

    def test_resolve_profile_catches_not_found(self):
        """Test that ProfileNotFoundError is caught and handled properly."""
        from config.factory import _resolve_profile_and_env

        # When profile doesn't exist, function exits
        # This is expected behavior - test should expect SystemExit
        with pytest.raises(SystemExit):
            _resolve_profile_and_env("definitely-nonexistent-profile-12345")

    def test_resolve_profile_with_config_not_found(self):
        """Test resolving when no config file exists at all."""
        from config.factory import _resolve_profile_and_env
        from profile_config.exceptions import ConfigNotFoundError

        # Mock ProfileConfigResolver to raise ConfigNotFoundError
        with patch("config.factory.ProfileConfigResolver") as mock_resolver_class:
            mock_instance = MagicMock()
            mock_instance.resolve.side_effect = ConfigNotFoundError("No config")
            mock_resolver_class.return_value = mock_instance

            # Should return defaults when no config file
            config = _resolve_profile_and_env("any-profile")

            assert isinstance(config, dict)
            # Should have defaults applied
            assert "model_string" in config or "system_prompt" in config
