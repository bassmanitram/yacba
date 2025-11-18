"""
Tests for utils.general_utils module.

Target Coverage: 90%+
"""

import pytest
from datetime import datetime
import json


class TestCleanDict:
    """Tests for clean_dict function."""

    def test_clean_dict_removes_none(self):
        """Test that None values are removed."""
        from utils.general_utils import clean_dict

        d = {"a": 1, "b": None, "c": "value", "d": None}
        result = clean_dict(d)

        assert "a" in result
        assert "c" in result
        assert "b" not in result
        assert "d" not in result
        assert result == {"a": 1, "c": "value"}

    def test_clean_dict_empty(self):
        """Test cleaning empty dict."""
        from utils.general_utils import clean_dict

        result = clean_dict({})
        assert result == {}

    def test_clean_dict_all_none(self):
        """Test cleaning dict with all None values."""
        from utils.general_utils import clean_dict

        d = {"a": None, "b": None}
        result = clean_dict(d)
        assert result == {}

    def test_clean_dict_no_none(self):
        """Test cleaning dict with no None values."""
        from utils.general_utils import clean_dict

        d = {"a": 1, "b": 2, "c": "value"}
        result = clean_dict(d)
        assert result == d

    def test_clean_dict_preserves_falsy(self):
        """Test that falsy non-None values are preserved."""
        from utils.general_utils import clean_dict

        d = {"zero": 0, "empty_str": "", "false": False, "none": None, "empty_list": []}
        result = clean_dict(d)

        assert "zero" in result
        assert result["zero"] == 0
        assert "empty_str" in result
        assert result["empty_str"] == ""
        assert "false" in result
        assert result["false"] is False
        assert "empty_list" in result
        assert result["empty_list"] == []
        assert "none" not in result


class TestCustomJsonSerializer:
    """Tests for custom_json_serializer_for_display function."""

    def test_serialize_datetime(self):
        """Test serializing datetime objects."""
        from utils.general_utils import custom_json_serializer_for_display

        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = custom_json_serializer_for_display(dt)

        assert isinstance(result, str)
        assert "2024" in result
        assert "01" in result or "1" in result
        assert "15" in result

    def test_serialize_bytes_short(self):
        """Test serializing short bytes objects."""
        from utils.general_utils import custom_json_serializer_for_display

        data = b"Hello, World!"
        result = custom_json_serializer_for_display(data)

        assert isinstance(result, str)
        assert "Hello" in result
        assert "World" in result

    def test_serialize_bytes_long(self):
        """Test serializing long bytes objects (should truncate)."""
        from utils.general_utils import custom_json_serializer_for_display
        from utils.general_utils import MAX_BYTES_LENGTH_FOR_DISPLAY, ELLIPSIS

        # Create bytes longer than MAX_BYTES_LENGTH_FOR_DISPLAY
        data = b"A" * (MAX_BYTES_LENGTH_FOR_DISPLAY + 50)
        result = custom_json_serializer_for_display(data)

        assert isinstance(result, str)
        assert len(result) <= MAX_BYTES_LENGTH_FOR_DISPLAY + len(ELLIPSIS)
        assert result.endswith(ELLIPSIS)

    def test_serialize_unsupported_type_raises(self):
        """Test that unsupported types raise TypeError."""
        from utils.general_utils import custom_json_serializer_for_display

        # Try to serialize an unsupported type
        unsupported = object()

        with pytest.raises(TypeError, match="not JSON serializable"):
            custom_json_serializer_for_display(unsupported)

    def test_serialize_with_json_dumps(self):
        """Test using serializer with json.dumps."""
        from utils.general_utils import custom_json_serializer_for_display

        data = {
            "timestamp": datetime(2024, 1, 15, 10, 30),
            "message": "Test",
            "data": b"Binary data",
        }

        # Should be able to serialize with our custom serializer
        result = json.dumps(data, default=custom_json_serializer_for_display)

        assert isinstance(result, str)
        assert "2024" in result
        assert "Test" in result
        assert "Binary" in result


class TestGeneralUtilsConstants:
    """Tests for module constants."""

    def test_max_bytes_length_constant(self):
        """Test MAX_BYTES_LENGTH_FOR_DISPLAY constant."""
        from utils.general_utils import MAX_BYTES_LENGTH_FOR_DISPLAY

        assert isinstance(MAX_BYTES_LENGTH_FOR_DISPLAY, int)
        assert MAX_BYTES_LENGTH_FOR_DISPLAY > 0

    def test_ellipsis_constant(self):
        """Test ELLIPSIS constant."""
        from utils.general_utils import ELLIPSIS

        assert isinstance(ELLIPSIS, str)
        assert len(ELLIPSIS) > 0

    def test_real_length_calculation(self):
        """Test REAL_LENGTH is correctly calculated."""
        from utils.general_utils import (
            REAL_LENGTH,
            MAX_BYTES_LENGTH_FOR_DISPLAY,
            ELLIPSIS,
        )

        assert REAL_LENGTH == MAX_BYTES_LENGTH_FOR_DISPLAY - len(ELLIPSIS)
        assert REAL_LENGTH > 0


@pytest.mark.integration
class TestGeneralUtilsIntegration:
    """Integration tests for general_utils."""

    def test_clean_and_serialize_workflow(self):
        """Test workflow of cleaning dict and serializing to JSON."""
        from utils.general_utils import clean_dict, custom_json_serializer_for_display

        # Create data with None values and special types
        data = {
            "id": 1,
            "name": "Test",
            "timestamp": datetime.now(),
            "data": b"Binary content",
            "optional": None,
            "another_optional": None,
        }

        # Clean None values
        cleaned = clean_dict(data)
        assert "optional" not in cleaned
        assert "another_optional" not in cleaned

        # Serialize to JSON
        json_str = json.dumps(cleaned, default=custom_json_serializer_for_display)
        assert isinstance(json_str, str)

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["id"] == 1
        assert parsed["name"] == "Test"
