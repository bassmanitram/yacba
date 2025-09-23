from typing import Any, Dict, List, Optional, Tuple

import litellm

from ._utils import recursively_remove
from yacba_types import Tool, Message
from loguru import logger


class DefaultAdapter:
    """
    Adapter for frameworks that support standard system prompts and message formats.
    Handles YACBA's responsibility for framework-specific configuration.
    """
    
    @property
    def expected_exceptions(self) -> Tuple[type[Exception], ...]:
        """Expected exception types that the CLI should catch for this framework."""
        return (
            litellm.exceptions.APIError,
            litellm.exceptions.APIConnectionError, 
            litellm.exceptions.ServiceUnavailableError,
            litellm.exceptions.Timeout
        )
    
    def adapt_tools(self, tools: List[Tool], model_string: str) -> List[Tool]:
        """
        Adapts tool schemas for the specific framework.
        For LiteLLM models, cleans the tool schemas to remove 'additionalProperties',
        which is not supported by some underlying APIs like Google VertexAI.
        
        Args:
            tools: List of tools to adapt
            model_string: Model string to determine adaptations needed
            
        Returns:
            List of adapted tools
        """
        if "litellm" in model_string:
            logger.debug("LiteLLM model detected. Cleaning tool schemas to remove 'additionalProperties'.")
            for tool in tools:
                if hasattr(tool, 'tool_spec'):
                    recursively_remove(tool.tool_spec, "additionalProperties")
        return tools

    def prepare_agent_args(
        self, 
        system_prompt: str, 
        messages: List[Message], 
        startup_files_content: Optional[List[Message]], 
        emulate_system_prompt: bool = False
    ) -> Dict[str, Any]:
        """
        Prepares the arguments for the Agent constructor.
        Handles YACBA's responsibility for message preparation and system prompt handling.
        
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
        
        # Handle system prompt emulation for frameworks that don't support it natively
        if emulate_system_prompt and system_prompt:
            logger.debug("Emulating system prompt by prepending to the first user message as requested.")
            first_user_msg_index = next((i for i, msg in enumerate(messages) if msg["role"] == "user"), -1)

            if first_user_msg_index != -1:
                current_content = messages[first_user_msg_index]["content"]
                if isinstance(current_content, list):
                    messages[first_user_msg_index]["content"].insert(0, {"type": "text", "text": system_prompt})
                else:
                    messages[first_user_msg_index]["content"] = f"{system_prompt}\n\n{current_content}"
            else:
                messages.insert(0, {"role": "user", "content": [{"type": "text", "text": system_prompt}]})
            
            return {"system_prompt": None, "messages": messages}

        return {"system_prompt": system_prompt, "messages": messages}

    def transform_content(self, content: Any) -> Any:
        """
        Transforms message content for the specific framework.
        Default implementation passes content through unchanged.
        
        Args:
            content: Content to transform
            
        Returns:
            Transformed content
        """
        return content

