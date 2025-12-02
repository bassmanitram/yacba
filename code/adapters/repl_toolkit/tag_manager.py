"""
Tag management for YACBA conversation positions.

Provides tagging functionality to mark and restore conversation positions.
Tags are ephemeral (yacba session-only) and validated using message content hashes.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from strands.types.content import Message

from utils.logging import get_logger

logger = get_logger(__name__)


def compute_message_hash(message: Message) -> str:
    """Compute a stable hash of a message's content.
    
    Args:
        message: The message to hash
        
    Returns:
        SHA256 hash of message content (first 16 characters)
    """
    # Use json.dumps with sorted keys for stable serialization
    # Only hash the content, not role or other metadata
    message_str = json.dumps(message.get("content", []), sort_keys=True)
    hash_obj = hashlib.sha256(message_str.encode())
    return hash_obj.hexdigest()[:16]


def is_user_input_message(message: Message) -> bool:
    """Check if message is a user input (not a tool result).
    
    User input messages have role="user" and do NOT contain toolResult blocks.
    Tool result messages have role="user" but DO contain toolResult blocks.
    
    Args:
        message: Message to check
        
    Returns:
        True if this is user input, False if tool result or assistant message
    """
    if message.get("role") != "user":
        return False
    
    # Check content blocks - if ANY block is toolResult, it's not user input
    content = message.get("content", [])
    for block in content:
        if "toolResult" in block:
            return False
    
    # It's a user message with no tool results
    return True


@dataclass
class Tag:
    """Represents a conversation position tag.
    
    Attributes:
        name: Tag name (user-defined or auto-generated)
        position: Absolute message index in conversation
        message_hash: Hash of message content for validation
        timestamp: When tag was created
        is_special: Whether this is a special system tag
    """
    name: str
    position: int
    message_hash: str
    timestamp: datetime
    is_special: bool = False
    
    def validate_against_messages(
        self, 
        messages: List[Message]
    ) -> Tuple[bool, Optional[str]]:
        """Check if this tag still points to the correct message.
        
        Special tags (like __session_start__) are ALWAYS valid as positional markers.
        
        Args:
            messages: Current message array
            
        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, error_message) if invalid
        """
        # Special tags are ALWAYS valid - they're positional markers, not content validators
        if self.is_special:
            # Just verify position is in range
            if self.position < 0 or self.position > len(messages):
                return False, f"Position {self.position} out of range (0-{len(messages)})"
            return True, None
        
        # Check if position exists
        if self.position < 0 or self.position > len(messages):
            return False, f"Position {self.position} out of range (0-{len(messages)})"
        
        # Special case: end of conversation marker
        if self.message_hash == "END_OF_CONVERSATION":
            if self.position == len(messages):
                return True, None
            else:
                return False, "Tag pointed to end of conversation, but conversation has changed"
        
        # Check if position is at the end (valid for undo)
        if self.position == len(messages):
            return True, None
        
        # Validate hash matches
        current_message = messages[self.position]
        current_hash = compute_message_hash(current_message)
        
        if current_hash == self.message_hash:
            return True, None
        else:
            return False, f"Message at position {self.position} has changed (hash mismatch)"


class TagManager:
    """Manages conversation position tags.
    
    Tags are ephemeral (in-memory only) and validated lazily (on use).
    Special tags like __session_start__ have restricted behavior.
    """
    
    def __init__(self):
        """Initialize the tag manager."""
        self.tags: Dict[str, Tag] = {}
        self._anonymous_counter = 0
        logger.debug("tag_manager_initialized")
    
    def create_session_start_tag(self, position: int = 0) -> str:
        """Create or recreate the special __session_start__ tag.
        
        This tag marks the beginning of the session and is automatically
        managed by clear operations. It is ALWAYS valid as a positional marker.
        
        Args:
            position: Position for session start (typically 0)
            
        Returns:
            Tag name (__session_start__)
        """
        self.tags["__session_start__"] = Tag(
            name="__session_start__",
            position=position,
            message_hash="SESSION_START",  # Special marker (not validated)
            timestamp=datetime.now(),
            is_special=True
        )
        logger.debug("session_start_tag_created", position=position)
        return "__session_start__"
    
    def set_tag(
        self, 
        name: str, 
        position: int, 
        messages: List[Message]
    ) -> str:
        """Create or replace a tag with hash validation.
        
        Args:
            name: Tag name
            position: Message index to tag
            messages: Current message array (for hash computation)
            
        Returns:
            Tag name
            
        Raises:
            ValueError: If position is invalid or name is reserved
        """
        if name == "__session_start__":
            raise ValueError("Cannot overwrite __session_start__ tag")
        
        if position < 0 or position > len(messages):
            raise ValueError(
                f"Invalid position {position} (0-{len(messages)} allowed)"
            )
        
        # Compute hash of message at this position
        # Handle edge case: position == len(messages) (tag points "after" last message)
        if position < len(messages):
            message_hash = compute_message_hash(messages[position])
        else:
            message_hash = "END_OF_CONVERSATION"  # Special marker
        
        self.tags[name] = Tag(
            name=name,
            position=position,
            message_hash=message_hash,
            timestamp=datetime.now(),
            is_special=False
        )
        
        logger.debug("tag_created", name=name, position=position)
        return name
    
    def generate_anonymous_tag(
        self, 
        position: int, 
        messages: List[Message]
    ) -> str:
        """Generate an anonymous tag with auto-incremented name.
        
        Args:
            position: Message index to tag
            messages: Current message array
            
        Returns:
            Generated tag name (e.g., "tag_1", "tag_2")
        """
        self._anonymous_counter += 1
        name = f"tag_{self._anonymous_counter}"
        return self.set_tag(name, position, messages)
    
    def get_tag(self, name: str) -> Optional[Tag]:
        """Get a tag by name.
        
        Args:
            name: Tag name
            
        Returns:
            Tag object or None if not found
        """
        return self.tags.get(name)
    
    def list_tags(self) -> List[Tag]:
        """Get all tags sorted by position.
        
        Returns:
            List of Tag objects sorted by position
        """
        return sorted(self.tags.values(), key=lambda t: t.position)
    
    def remove_tag(self, name: str) -> bool:
        """Remove a tag by name.
        
        Args:
            name: Tag name to remove
            
        Returns:
            True if tag was removed, False if not found
        """
        if name in self.tags:
            del self.tags[name]
            logger.debug("tag_removed", name=name)
            return True
        return False
    
    def remove_tags_beyond_position(self, max_position: int) -> List[str]:
        """Remove all tags pointing beyond a given position.
        
        This is used when undoing removes messages, invalidating tags
        that pointed to those messages.
        
        Args:
            max_position: Maximum valid position (exclusive)
            
        Returns:
            List of removed tag names
        """
        removed = []
        tags_to_remove = []
        
        for name, tag in self.tags.items():
            if tag.position >= max_position:
                tags_to_remove.append(name)
                removed.append(name)
        
        for name in tags_to_remove:
            del self.tags[name]
        
        if removed:
            logger.debug(
                "tags_removed_beyond_position", 
                max_position=max_position, 
                count=len(removed)
            )
        
        return removed
    
    def clear_user_tags(self) -> int:
        """Clear all user-defined tags (keep special tags).
        
        Returns:
            Number of tags removed
        """
        tags_to_remove = [
            name for name, tag in self.tags.items()
            if not tag.is_special
        ]
        
        for name in tags_to_remove:
            del self.tags[name]
        
        logger.debug("user_tags_cleared", count=len(tags_to_remove))
        return len(tags_to_remove)
    
    def validate_tag(
        self, 
        tag: Tag, 
        messages: List[Message]
    ) -> Tuple[bool, Optional[str]]:
        """Validate that a tag still points to the correct message.
        
        This is a convenience wrapper around Tag.validate_against_messages.
        
        Args:
            tag: The tag to validate
            messages: Current message array
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return tag.validate_against_messages(messages)
