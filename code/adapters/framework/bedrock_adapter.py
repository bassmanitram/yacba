from typing import Any, Dict, List, Optional, Tuple
from botocore.exceptions import ClientError
from loguru import logger
from yacba_types import Tool, Message

class BedrockAdapter:
    """
    Adapter for AWS Bedrock. This version uses a simple, direct transformation
    to ensure API compliance for text and image content, including loaded session data.
    Handles YACBA's responsibility for Bedrock-specific content formatting.
    """

    @property
    def expected_exceptions(self) -> Tuple[type[Exception], ...]:
        """Expected exception types that the CLI should catch for this framework."""
        return (ClientError,)

    def prepare_agent_args(
        self,
        system_prompt: str,
        messages: List[Message],
        startup_files_content: Optional[List[Message]],
        emulate_system_prompt: bool = False
    ) -> Dict[str, Any]:
        """
        Prepares the arguments for the Agent constructor with Bedrock-specific formatting.

        Args:
            system_prompt: System prompt to use
            messages: Existing message history
            startup_files_content: Optional startup file messages
            emulate_system_prompt: Whether to emulate system prompt in first user message

        Returns:
            Dictionary of arguments for Agent constructor
        """
        # Combine startup files with existing messages
        if startup_files_content:
            messages = startup_files_content + messages

        # Transform all messages for Bedrock compatibility
        transformed_messages = [
            {"role": msg["role"], "content": self._adapt_message_content(msg["content"])}
            for msg in messages if msg.get("role") and "content" in msg and msg["content"] is not None
        ]

        # Handle system prompt emulation for Bedrock
        if emulate_system_prompt and system_prompt:
            logger.debug("Emulating system prompt by prepending to the first user message as requested.")
            first_user_msg_index = next((i for i, msg in enumerate(transformed_messages) if msg["role"] == "user"), -1)

            if first_user_msg_index != -1:
                transformed_messages[first_user_msg_index]["content"].insert(0, {"text": system_prompt})
            else:
                transformed_messages.insert(0, {"role": "user", "content": [{"text": system_prompt}]})

            return {"system_prompt": None, "messages": [m for m in transformed_messages if m["content"]]}

        return {"system_prompt": system_prompt, "messages": [m for m in transformed_messages if m["content"]]}

    def transform_content(self, content: Any) -> List[Dict[str, Any]]:
        """
        Transforms message content for Bedrock compatibility.

        Args:
            content: Content to transform

        Returns:
            Bedrock-compatible content blocks
        """
        return self._adapt_message_content(content)

    def adapt_tools(self, tools: List[Tool], model_string: str) -> List[Tool]:
        """
        Adapts tools for Bedrock compatibility.

        Args:
            tools: List of tools to adapt
            model_string: Model string (unused for Bedrock)

        Returns:
            List of adapted tools (unchanged for Bedrock)
        """
        return tools

    def _adapt_message_content(self, content: Any) -> List[Dict[str, Any]]:
        """
        Rigorously transforms message content into the strict format required by the
        Bedrock Converse API. It handles text and image blocks from any source
        (new files or session history) and replaces invalid binary files with a placeholder.

        Args:
            content: Content to adapt

        Returns:
            List of Bedrock-compatible content blocks
        """
        if not isinstance(content, list):
            return [{"text": str(content)}] if content else []

        VALID_IMAGE_FORMATS = {'gif', 'jpeg', 'png', 'webp'}
        transformed_list = []

        for block in content:
            if not isinstance(block, dict):
                continue

            # Case 1: Handle text blocks in any format
            if block.get("type") == "text" or "text" in block:
                transformed_list.append({"text": block.get("text", "")})
                continue

            # Case 2: Handle image blocks in the 'strands' format
            if block.get("type") == "image" and "source" in block:
                source = block.get("source", {})
                media_type = source.get("media_type", "")
                image_format = media_type.split('/')[-1] if '/' in media_type else ''

                if image_format in VALID_IMAGE_FORMATS and source.get("data"):
                    transformed_list.append({
                        "image": {
                            "format": image_format,
                            "source": {"bytes": source.get("data")}
                        }
                    })
                else:
                    logger.warning(f"File with media type '{media_type}' is not a supported image format for Bedrock. Representing as a text placeholder.")
                    transformed_list.append({
                        "text": f"[User uploaded a binary file of type '{media_type}' that cannot be displayed.]"
                    })
                continue

            # Case 3: Handle image blocks that might be in a partial/historical Bedrock format
            if "image" in block and isinstance(block["image"], dict):
                image_data = block["image"]
                image_format = image_data.get("format", "")

                if image_format in VALID_IMAGE_FORMATS and "source" in image_data and "bytes" in image_data["source"]:
                    transformed_list.append(block)  # It's already valid
                else:
                    media_type = f"image/{image_format}" if image_format else "unknown"
                    logger.warning(f"Historical file with media type '{media_type}' is not a supported image format for Bedrock. Representing as a text placeholder.")
                    transformed_list.append({
                        "text": f"[User uploaded a binary file of type '{media_type}' that cannot be displayed.]"
                    })
                continue

        return transformed_list
