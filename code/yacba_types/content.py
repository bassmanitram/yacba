"""
Content and message type definitions.
"""

from typing import Dict, List, Union, Literal, Optional
from typing_extensions import TypedDict
from .base import JSONDict

# Content block types
class TextBlock(TypedDict):
    """Text content block."""
    type: Literal["text"]
    text: str

class ImageSource(TypedDict):
    """Image source data."""
    type: Literal["base64"]
    media_type: str
    data: str

class ImageBlock(TypedDict):
    """Image content block."""
    type: Literal["image"]
    source: ImageSource

# Bedrock-specific image format
class BedrockImageSource(TypedDict):
    """Bedrock image source format."""
    bytes: str

class BedrockImageBlock(TypedDict):
    """Bedrock image block format."""
    image: Dict[str, Union[str, BedrockImageSource]]

# Union of all content block types
ContentBlock = Union[TextBlock, ImageBlock, BedrockImageBlock]

# Message content can be string or list of blocks
MessageContent = Union[str, List[ContentBlock]]

# Complete message structure
class Message(TypedDict):
    """Complete message structure."""
    role: Literal["user", "assistant", "system"]
    content: MessageContent

# File processing types
class ProcessedFile(TypedDict):
    """Result of file processing."""
    path: str
    mimetype: str
    content_block: ContentBlock
    error: Optional[str]

# Input parsing types
class FileReference(TypedDict):
    """File reference from user input."""
    path: str
    mimetype: Optional[str]
    start_pos: int
    end_pos: int
