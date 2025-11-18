"""
Tests for yacba_types module.

Target Coverage: 95%+
"""

import pytest
from pathlib import Path


class TestExitCode:
    """Tests for ExitCode enum."""

    def test_exit_code_values(self):
        """Test that exit codes have expected values."""
        from yacba_types import ExitCode

        assert ExitCode.SUCCESS == 0
        assert ExitCode.CONFIG_ERROR == 1
        assert ExitCode.INITIALIZATION_ERROR == 2
        assert ExitCode.RUNTIME_ERROR == 3
        assert ExitCode.INTERRUPTED == 4
        assert ExitCode.FATAL_ERROR == 5

    def test_exit_code_is_int(self):
        """Test that exit codes are integers."""
        from yacba_types import ExitCode

        assert isinstance(ExitCode.SUCCESS, int)
        assert isinstance(ExitCode.CONFIG_ERROR, int)

    def test_exit_code_unique(self):
        """Test that all exit codes are unique."""
        from yacba_types import ExitCode

        values = [code.value for code in ExitCode]
        assert len(values) == len(set(values))

    def test_exit_code_enum_iteration(self):
        """Test iterating over exit codes."""
        from yacba_types import ExitCode

        codes = list(ExitCode)
        assert len(codes) == 6
        assert ExitCode.SUCCESS in codes


class TestTypeAliases:
    """Tests for type alias definitions."""

    def test_json_value_import(self):
        """Test JSONValue type alias is importable."""
        from yacba_types import JSONValue

        assert JSONValue is not None

    def test_json_dict_import(self):
        """Test JSONDict type alias is importable."""
        from yacba_types import JSONDict

        assert JSONDict is not None

    def test_path_like_import(self):
        """Test PathLike type alias is importable."""
        from yacba_types import PathLike

        assert PathLike is not None

    def test_path_like_usage(self):
        """Test PathLike can represent different path types."""
        from yacba_types import PathLike

        def accepts_path_like(p: PathLike) -> str:
            return str(p)

        # Should work with string
        assert accepts_path_like("string/path") == "string/path"
        # Should work with Path
        assert accepts_path_like(Path("/test")) == "/test"


class TestContentTypes:
    """Tests for content type definitions."""

    def test_content_block_import(self):
        """Test ContentBlock is importable."""
        from yacba_types import ContentBlock

        assert ContentBlock is not None

    def test_text_block_import(self):
        """Test TextBlock is importable."""
        from yacba_types import TextBlock

        assert TextBlock is not None

    def test_image_block_import(self):
        """Test ImageBlock is importable."""
        from yacba_types import ImageBlock

        assert ImageBlock is not None

    def test_message_content_import(self):
        """Test MessageContent is importable."""
        from yacba_types import MessageContent

        assert MessageContent is not None

    def test_message_import(self):
        """Test Message is importable."""
        from yacba_types import Message

        assert Message is not None


class TestConfigTypes:
    """Tests for configuration-related types."""

    def test_tool_discovery_result_import(self):
        """Test ToolDiscoveryResult is importable."""
        from yacba_types import ToolDiscoveryResult

        assert ToolDiscoveryResult is not None

    def test_session_data_import(self):
        """Test SessionData is importable."""
        from yacba_types import SessionData

        assert SessionData is not None

    def test_file_upload_import(self):
        """Test FileUpload is importable."""
        from yacba_types import FileUpload

        assert FileUpload is not None


@pytest.mark.unit
class TestTypeSystemIntegration:
    """Integration tests for the type system."""

    def test_all_exported_types_importable(self):
        """Test that all types can be imported from yacba_types."""
        from yacba_types import (
            ExitCode,
            JSONValue,
            JSONDict,
            PathLike,
            ToolDiscoveryResult,
            SessionData,
            FileUpload,
            ContentBlock,
            TextBlock,
            ImageBlock,
            MessageContent,
            Message,
        )

        # Verify they're all importable
        assert all(
            [
                ExitCode,
                JSONValue,
                JSONDict,
                PathLike,
                ToolDiscoveryResult,
                SessionData,
                FileUpload,
                ContentBlock,
                TextBlock,
                ImageBlock,
                MessageContent,
                Message,
            ]
        )

    def test_exit_code_in_exception_handling(self):
        """Test using ExitCode in exception handling."""
        from yacba_types import ExitCode

        def might_fail(should_fail: bool) -> int:
            if should_fail:
                return ExitCode.RUNTIME_ERROR
            return ExitCode.SUCCESS

        assert might_fail(False) == ExitCode.SUCCESS
        assert might_fail(True) == ExitCode.RUNTIME_ERROR

    def test_module_has_all_attribute(self):
        """Test that yacba_types defines __all__."""
        import yacba_types

        assert hasattr(yacba_types, "__all__")
        assert len(yacba_types.__all__) > 0

    def test_all_in_all_are_importable(self):
        """Test that everything in __all__ can actually be imported."""
        import yacba_types

        for name in yacba_types.__all__:
            assert hasattr(yacba_types, name), f"{name} in __all__ but not importable"
