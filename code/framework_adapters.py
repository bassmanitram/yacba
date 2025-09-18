# framework_adapters.py
# Contains adapter classes to handle framework-specific logic.

from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
import litellm
from botocore.exceptions import ClientError

class FrameworkAdapter:
    """Base class for framework-specific adapters."""
    
    @property
    def expected_exceptions(self) -> Tuple[type[Exception], ...]:
        """A tuple of exception types that the CLI should catch for this framework."""
        return (Exception,) # Default to catching everything if not specified

    def prepare_agent_args(self, system_prompt: str, messages: List[Dict[str, Any]], startup_files_content: Optional[List[Dict[str, Any]]], emulate_system_prompt: bool = False) -> Dict[str, Any]:
        """Prepares the arguments for the Agent constructor."""
        raise NotImplementedError

    def transform_content(self, content: Any) -> Any:
        """Transforms message content for the specific framework."""
        return content

class DefaultAdapter(FrameworkAdapter):
    """Adapter for frameworks that support standard system prompts and message formats."""
    
    @property
    def expected_exceptions(self) -> Tuple[type[Exception], ...]:
        return (
            litellm.exceptions.APIError,
            litellm.exceptions.APIConnectionError, 
            litellm.exceptions.ServiceUnavailableError,
            litellm.exceptions.Timeout
        )

    def prepare_agent_args(self, system_prompt: str, messages: List[Dict[str, Any]], startup_files_content: Optional[List[Dict[str, Any]]], emulate_system_prompt: bool = False) -> Dict[str, Any]:
        if startup_files_content:
            messages = startup_files_content + messages
        
        if emulate_system_prompt and system_prompt:
            logger.debug("Emulating system prompt by prepending to the first user message as requested.")
            first_user_msg_index = next((i for i, msg in enumerate(messages) if msg["role"] == "user"), -1)

            if first_user_msg_index != -1:
                # Prepend to existing user message
                current_content = messages[first_user_msg_index]["content"]
                if isinstance(current_content, list):
                    messages[first_user_msg_index]["content"].insert(0, {"type": "text", "text": system_prompt})
                else: # Handle plain string content
                    messages[first_user_msg_index]["content"] = f"{system_prompt}\n\n{current_content}"
            else:
                # Create a new user message if none exists
                messages.insert(0, {"role": "user", "content": [{"type": "text", "text": system_prompt}]})
            
            return {
                "system_prompt": None,
                "messages": messages
            }

        return {
            "system_prompt": system_prompt,
            "messages": messages
        }

class BedrockAdapter(FrameworkAdapter):
    """
    Adapter for AWS Bedrock. This version uses a simple, direct transformation
    to ensure API compliance for text and image content.
    """

    @property
    def expected_exceptions(self) -> Tuple[type[Exception], ...]:
        return (ClientError,)

    def prepare_agent_args(self, system_prompt: str, messages: List[Dict[str, Any]], startup_files_content: Optional[List[Dict[str, Any]]], emulate_system_prompt: bool = False) -> Dict[str, Any]:
        """
        Prepares agent arguments for Bedrock by transforming the message history
        into the correct format. It passes the system prompt directly, unless
        emulation is requested by the user.
        """
        if startup_files_content:
            messages = startup_files_content + messages

        # Transform the entire message history to be Bedrock-compliant.
        transformed_messages = []
        for msg in messages:
            if msg.get("role") and "content" in msg and msg["content"] is not None:
                # Adapt the content of each message
                adapted_content = self._adapt_message_content(msg["content"])
                # ONLY add the message if the content is not empty after adaptation
                if adapted_content:
                    transformed_messages.append({
                        "role": msg["role"],
                        "content": adapted_content
                    })
        
        # Conditionally emulate the system prompt if the flag is set.
        if emulate_system_prompt and system_prompt:
            logger.debug("Emulating system prompt by prepending to the first user message as requested.")
            first_user_msg_index = next((i for i, msg in enumerate(transformed_messages) if msg["role"] == "user"), -1)

            if first_user_msg_index != -1:
                transformed_messages[first_user_msg_index]["content"].insert(0, {"text": system_prompt})
            else:
                transformed_messages.insert(0, {"role": "user", "content": [{"text": system_prompt}]})
            
            return {
                "system_prompt": None,
                "messages": transformed_messages
            }

        # The Bedrock Converse API supports system prompts, so we pass it directly.
        # Model-specific workarounds are no longer handled at the adapter level.
        return {
            "system_prompt": system_prompt,
            "messages": transformed_messages
        }

    def transform_content(self, content: Any) -> List[Dict[str, Any]]:
        """
        Public method to transform new, incoming content.
        """
        return self._adapt_message_content(content)

    def _adapt_message_content(self, content: Any) -> List[Dict[str, Any]]:
        """
        Transforms message content into the simple, strict format required by the
        Bedrock Converse API. It handles text and image blocks.
        """
        if not isinstance(content, list):
            return [{"text": str(content)}]

        transformed_list = []
        for block in content:
            if not isinstance(block, dict):
                continue

            # Case 1: The block is in the 'strands' format with a 'type' key.
            if "type" in block:
                if block["type"] == "text":
                    transformed_list.append({"text": block.get("text", "")})
                elif block["type"] == "image":
                    source = block.get("source", {})
                    if source.get("type") == "base64":
                        media_type = source.get("media_type", "image/jpeg")
                        image_format = media_type.split('/')[-1] if '/' in media_type else 'jpeg'
                        data = source.get("data")
                        if data:
                            transformed_list.append({"image": {"format": image_format, "source": {"bytes": data}}})
            
            # Case 2: The block might already be in Bedrock format (no 'type' key).
            # We pass it through to avoid dropping it.
            elif any(key in block for key in ["text", "image"]):
                transformed_list.append(block)
        
        return transformed_list


