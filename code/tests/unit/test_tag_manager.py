"""
Unit tests for TagManager.
"""

import pytest
from datetime import datetime

from adapters.repl_toolkit.tag_manager import (
    TagManager,
    Tag,
    compute_message_hash,
    is_user_input_message,
)


class TestMessageHashing:
    """Test message hash computation."""
    
    def test_compute_message_hash(self):
        """Test hash computation for a message."""
        message = {
            "role": "user",
            "content": [{"text": "Hello"}]
        }
        
        hash1 = compute_message_hash(message)
        hash2 = compute_message_hash(message)
        
        assert hash1 == hash2
        assert len(hash1) == 16
    
    def test_different_messages_different_hashes(self):
        """Test that different messages produce different hashes."""
        message1 = {"role": "user", "content": [{"text": "Hello"}]}
        message2 = {"role": "user", "content": [{"text": "World"}]}
        
        hash1 = compute_message_hash(message1)
        hash2 = compute_message_hash(message2)
        
        assert hash1 != hash2
    
    def test_role_not_included_in_hash(self):
        """Test that role is not included in hash (only content)."""
        message1 = {"role": "user", "content": [{"text": "Hello"}]}
        message2 = {"role": "assistant", "content": [{"text": "Hello"}]}
        
        hash1 = compute_message_hash(message1)
        hash2 = compute_message_hash(message2)
        
        # Same content, different roles = same hash (only content hashed)
        assert hash1 == hash2


class TestUserInputDetection:
    """Test user input message detection."""
    
    def test_user_text_message(self):
        """Test that user text messages are detected."""
        message = {"role": "user", "content": [{"text": "Hello"}]}
        assert is_user_input_message(message) is True
    
    def test_tool_result_message(self):
        """Test that tool result messages are NOT user input."""
        message = {
            "role": "user",
            "content": [{"toolResult": {"toolUseId": "1", "content": []}}]
        }
        assert is_user_input_message(message) is False
    
    def test_assistant_message(self):
        """Test that assistant messages are NOT user input."""
        message = {"role": "assistant", "content": [{"text": "Hi"}]}
        assert is_user_input_message(message) is False
    
    def test_mixed_content_with_tool_result(self):
        """Test that any tool result in content makes it NOT user input."""
        message = {
            "role": "user",
            "content": [
                {"text": "Some text"},
                {"toolResult": {"toolUseId": "1", "content": []}}
            ]
        }
        assert is_user_input_message(message) is False


class TestTagValidation:
    """Test tag validation logic."""
    
    def test_valid_tag(self):
        """Test validation of a valid tag."""
        messages = [
            {"role": "user", "content": [{"text": "Hello"}]},
            {"role": "assistant", "content": [{"text": "Hi"}]},
        ]
        
        tag = Tag(
            name="test",
            position=0,
            message_hash=compute_message_hash(messages[0]),
            timestamp=datetime.now(),
            is_special=False
        )
        
        is_valid, error = tag.validate_against_messages(messages)
        assert is_valid is True
        assert error is None
    
    def test_invalid_position_out_of_range(self):
        """Test validation fails for out of range position."""
        messages = [
            {"role": "user", "content": [{"text": "Hello"}]},
        ]
        
        tag = Tag(
            name="test",
            position=5,
            message_hash="somehash",
            timestamp=datetime.now(),
            is_special=False
        )
        
        is_valid, error = tag.validate_against_messages(messages)
        assert is_valid is False
        assert "out of range" in error.lower()
    
    def test_invalid_hash_mismatch(self):
        """Test validation fails for hash mismatch."""
        messages = [
            {"role": "user", "content": [{"text": "Hello"}]},
            {"role": "assistant", "content": [{"text": "Hi"}]},
        ]
        
        tag = Tag(
            name="test",
            position=0,
            message_hash="wronghash12345",
            timestamp=datetime.now(),
            is_special=False
        )
        
        is_valid, error = tag.validate_against_messages(messages)
        assert is_valid is False
        assert "hash mismatch" in error.lower()
    
    def test_end_of_conversation_marker(self):
        """Test validation of end of conversation marker."""
        messages = [
            {"role": "user", "content": [{"text": "Hello"}]},
        ]
        
        tag = Tag(
            name="test",
            position=1,
            message_hash="END_OF_CONVERSATION",
            timestamp=datetime.now(),
            is_special=False
        )
        
        is_valid, error = tag.validate_against_messages(messages)
        assert is_valid is True
        assert error is None
    
    def test_tag_at_end_position(self):
        """Test that tags at len(messages) are valid."""
        messages = [
            {"role": "user", "content": [{"text": "Hello"}]},
        ]
        
        tag = Tag(
            name="test",
            position=1,
            message_hash="anyhash",
            timestamp=datetime.now(),
            is_special=False
        )
        
        is_valid, error = tag.validate_against_messages(messages)
        assert is_valid is True
        assert error is None


class TestTagManager:
    """Test TagManager functionality."""
    
    def test_initialization(self):
        """Test tag manager initialization."""
        tm = TagManager()
        assert len(tm.tags) == 0
        assert tm._anonymous_counter == 0
    
    def test_create_session_start_tag(self):
        """Test creation of session start tag."""
        tm = TagManager()
        name = tm.create_session_start_tag(0)
        
        assert name == "__session_start__"
        assert "__session_start__" in tm.tags
        
        tag = tm.tags["__session_start__"]
        assert tag.position == 0
        assert tag.is_special is True
        assert tag.message_hash == "SESSION_START"
    
    def test_set_tag(self):
        """Test creating a user tag."""
        tm = TagManager()
        messages = [
            {"role": "user", "content": [{"text": "Hello"}]},
            {"role": "assistant", "content": [{"text": "Hi"}]},
        ]
        
        name = tm.set_tag("mytag", 1, messages)
        
        assert name == "mytag"
        assert "mytag" in tm.tags
        
        tag = tm.tags["mytag"]
        assert tag.position == 1
        assert tag.is_special is False
        assert len(tag.message_hash) == 16
    
    def test_cannot_overwrite_session_start(self):
        """Test that session start tag cannot be overwritten."""
        tm = TagManager()
        tm.create_session_start_tag(0)
        
        messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        
        with pytest.raises(ValueError, match="Cannot overwrite"):
            tm.set_tag("__session_start__", 0, messages)
    
    def test_invalid_position_raises_error(self):
        """Test that invalid positions raise errors."""
        tm = TagManager()
        messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        
        with pytest.raises(ValueError, match="Invalid position"):
            tm.set_tag("mytag", 5, messages)
        
        with pytest.raises(ValueError, match="Invalid position"):
            tm.set_tag("mytag", -1, messages)
    
    def test_tag_at_end_of_conversation(self):
        """Test tagging at end of conversation (position == len(messages))."""
        tm = TagManager()
        messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        
        name = tm.set_tag("end", 1, messages)
        tag = tm.tags[name]
        
        assert tag.position == 1
        assert tag.message_hash == "END_OF_CONVERSATION"
    
    def test_generate_anonymous_tag(self):
        """Test anonymous tag generation."""
        tm = TagManager()
        messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        
        name1 = tm.generate_anonymous_tag(0, messages)
        name2 = tm.generate_anonymous_tag(0, messages)
        
        assert name1 == "tag_1"
        assert name2 == "tag_2"
        assert name1 in tm.tags
        assert name2 in tm.tags
    
    def test_get_tag(self):
        """Test getting a tag by name."""
        tm = TagManager()
        messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        
        tm.set_tag("mytag", 0, messages)
        
        tag = tm.get_tag("mytag")
        assert tag is not None
        assert tag.name == "mytag"
        
        tag = tm.get_tag("nonexistent")
        assert tag is None
    
    def test_list_tags(self):
        """Test listing tags."""
        tm = TagManager()
        messages = [
            {"role": "user", "content": [{"text": "1"}]},
            {"role": "user", "content": [{"text": "2"}]},
            {"role": "user", "content": [{"text": "3"}]},
        ]
        
        tm.set_tag("c", 2, messages)
        tm.set_tag("a", 0, messages)
        tm.set_tag("b", 1, messages)
        
        tags = tm.list_tags()
        
        # Should be sorted by position
        assert len(tags) == 3
        assert tags[0].name == "a"
        assert tags[1].name == "b"
        assert tags[2].name == "c"
    
    def test_remove_tag(self):
        """Test removing a tag."""
        tm = TagManager()
        messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        
        tm.set_tag("mytag", 0, messages)
        assert "mytag" in tm.tags
        
        result = tm.remove_tag("mytag")
        assert result is True
        assert "mytag" not in tm.tags
        
        result = tm.remove_tag("nonexistent")
        assert result is False
    
    def test_remove_tags_beyond_position(self):
        """Test removing tags beyond a position."""
        tm = TagManager()
        messages = [
            {"role": "user", "content": [{"text": "1"}]},
            {"role": "user", "content": [{"text": "2"}]},
            {"role": "user", "content": [{"text": "3"}]},
            {"role": "user", "content": [{"text": "4"}]},
        ]
        
        tm.set_tag("a", 0, messages)
        tm.set_tag("b", 1, messages)
        tm.set_tag("c", 2, messages)
        tm.set_tag("d", 3, messages)
        
        removed = tm.remove_tags_beyond_position(2)
        
        assert len(removed) == 2
        assert "c" in removed
        assert "d" in removed
        assert "a" in tm.tags
        assert "b" in tm.tags
        assert "c" not in tm.tags
        assert "d" not in tm.tags
    
    def test_clear_user_tags(self):
        """Test clearing user tags while keeping special tags."""
        tm = TagManager()
        messages = [
            {"role": "user", "content": [{"text": "1"}]},
            {"role": "user", "content": [{"text": "2"}]},
        ]
        
        tm.create_session_start_tag(0)
        tm.set_tag("user1", 0, messages)
        tm.set_tag("user2", 1, messages)
        
        count = tm.clear_user_tags()
        
        assert count == 2
        assert "__session_start__" in tm.tags
        assert "user1" not in tm.tags
        assert "user2" not in tm.tags
    
    def test_special_tag_always_valid(self):
        """Test that special tags are ALWAYS valid regardless of content changes."""
        tm = TagManager()
        
        # Create messages and session start tag
        messages = [
            {"role": "user", "content": [{"text": "Original"}]},
            {"role": "assistant", "content": [{"text": "Response"}]},
        ]
        
        tm.create_session_start_tag(0)
        tag = tm.get_tag("__session_start__")
        
        # Initially valid
        is_valid, error = tm.validate_tag(tag, messages)
        assert is_valid is True
        assert error is None
        
        # Change the message at position 0
        messages[0] = {"role": "user", "content": [{"text": "COMPLETELY DIFFERENT"}]}
        
        # Special tag should STILL be valid (positional marker, not content validator)
        is_valid, error = tm.validate_tag(tag, messages)
        assert is_valid is True
        assert error is None
        
        # Regular tag with hash mismatch should fail
        regular_tag = Tag(
            name="regular",
            position=0,
            message_hash="wronghash",
            timestamp=datetime.now(),
            is_special=False
        )
        is_valid, error = regular_tag.validate_against_messages(messages)
        assert is_valid is False
        assert "hash mismatch" in error.lower()
