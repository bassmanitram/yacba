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

    def prepare_agent_args(self, system_prompt: str, messages: List[Dict[str, Any]], startup_files_content: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Prepares the arguments for the Agent constructor."""
        raise NotImplementedError

    def transform_content(self, content: Any) -> Any:
        """Transforms message content for the specific framework."""
        return content

class DefaultAdapter(FrameworkAdapter):
    """Adapter for frameworks that support standard system prompts and message formats."""
    
    @property
    def expected_exceptions(self) -> Tuple[type[Exception], ...]:
        return (litellm.exceptions.APIConnectionError, litellm.exceptions.ServiceUnavailableError)

    def prepare_agent_args(self, system_prompt: str, messages: List[Dict[str, Any]], startup_files_content: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        if startup_files_content:
            messages = startup_files_content + messages
        return {
            "system_prompt": system_prompt,
            "messages": messages
        }

class BedrockAdapter(FrameworkAdapter):
    """Adapter for AWS Bedrock, which has special requirements for system prompts and content."""

    @property
    def expected_exceptions(self) -> Tuple[type[Exception], ...]:
        return (ClientError,)

    def prepare_agent_args(self, system_prompt: str, messages: List[Dict[str, Any]], startup_files_content: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        if startup_files_content:
            messages = startup_files_content + messages

        if system_prompt:
            logger.debug("Prepending system prompt to user message for Bedrock compatibility.")
            if messages and messages[0]["role"] == "user":
                first_content = messages[0]["content"]
                if isinstance(first_content, list):
                    first_content.insert(0, {"text": system_prompt})
                else:
                    messages[0]["content"] = f"{system_prompt}\n\n{first_content}"
            else:
                messages.insert(0, {"role": "user", "content": [{"text": system_prompt}]})
        
        return {
            "system_prompt": None,
            "messages": [msg for msg in messages if msg.get("content")]
        }

    def transform_content(self, content: Any) -> Any:
        if isinstance(content, list):
            return [part for block in content for part in self._transform_block(block)]
        return content

    def _transform_block(self, block: Dict[str, Any]) -> List[Dict[str, Any]]:
        block_type = block.get("type")
        if block_type == "text":
            return [{"text": block.get("text", "")}]
        elif block_type == "image":
            return [{"image": {"source": block.get("source", {})}}]
        return [block]
