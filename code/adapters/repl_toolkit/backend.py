"""
Backend adapter implementing repl_toolkit protocols for strands_agent_factory.

This module provides the bridge between YACBA's strands_agent_factory Agent
and the repl_toolkit AsyncBackend protocol
"""

import types
from typing import Optional, List, Dict, Any

from utils.logging import get_logger
from utils.exceptions import log_exception

from strands_agent_factory.core.agent import AgentProxy
from strands_agent_factory import AgentFactoryConfig
from repl_toolkit import iter_content_parts
from repl_toolkit.ptypes import AsyncBackend
import base64

from .tag_manager import TagManager

logger = get_logger(__name__)


class YacbaBackend(AsyncBackend):
    """
    Adapter that wraps a strands_agent_factory AgentProxy to implement
    both AsyncBackend protocol for repl_toolkit.

    This allows YACBA to use repl_toolkit's interactive and headless
    interfaces while leveraging strands_agent_factory for agent management.
    """

    def __init__(
        self, agent_proxy: AgentProxy, config: Optional[AgentFactoryConfig] = None
    ):
        """
        Initialize the backend adapter.

        Args:
            agent_proxy: The strands_agent_factory AgentProxy instance
            config: The AgentFactoryConfig for status reporting
        """
        self.agent_proxy = agent_proxy
        self.config = config
        self.tag_manager = TagManager()
        
        # Initialize session start tag at position 0
        self.tag_manager.create_session_start_tag(0)
        
        logger.debug("yacba_backend_initialized")

    async def handle_input(self, user_input: str, images=None) -> bool:
        """
        Handle user input by processing it through the agent.

        This method implements both AsyncBackend an protocols
        by providing a unified interface for processing user input.

        Args:
            user_input: The input string from the user
            images: Optional list of images associated with the input

        Returns:
            bool: True if processing was successful, False otherwise
        """
        if not user_input.strip():
            logger.debug("empty_input_received")
            return True

        logger.debug("processing_user_input", preview=user_input[:100])

        try:
            if images:
                user_input = "".join(
                    (
                        f" image('{base64.b64encode(image.data).decode('ascii')}') "
                        if image
                        else content
                    )
                    for content, image in iter_content_parts(user_input, images)
                    if image or content
                )

            success = await self.agent_proxy.send_message_to_agent(
                user_input, show_user_input=False
            )
            if success:
                logger.debug("input_processed_successfully")
            else:
                logger.warning("input_processing_returned_false")

            return success

        except Exception as e:
            log_exception(logger, "error_processing_input", e)
            return False

    def get_agent_proxy(self) -> AgentProxy:
        """
        Get the underlying AgentProxy instance.

        This allows access to agent-specific functionality when needed
        by YACBA's command system or other components.

        Returns:
            AgentProxy: The wrapped agent proxy instance
        """
        return self.agent_proxy

    @property
    def is_ready(self) -> bool:
        """
        Check if the backend is ready to process input.

        Returns:
            bool: True if ready, False otherwise
        """
        # AgentProxy should be ready if it was created successfully
        return self.agent_proxy is not None

    def clear_conversation(self) -> bool:
        """
        Clear the conversation history and reset tags.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Clear messages
            self.agent_proxy.clear_messages()
            
            # Clear user tags and recreate session start
            self.tag_manager.clear_user_tags()
            self.tag_manager.create_session_start_tag(0)
            
            logger.debug("conversation_history_cleared")
            return True
        except Exception as e:
            log_exception(logger, "error_clearing_conversation", e)
            return False

    def get_tool_names(self) -> List[str]:
        """
        Get list of available tool names.

        Returns:
            List[str]: List of tool names
        """
        try:
            # Access tool_specs from AgentProxy - this should be available directly
            tool_specs = getattr(self.agent_proxy, "tool_specs", [])
            if not tool_specs:
                return []

            # Extract tool names from tool specs
            tool_names = []
            for tool_spec in tool_specs:
                if hasattr(tool_spec, "name"):
                    tool_names.append(tool_spec.name)
                elif isinstance(tool_spec, dict) and "name" in tool_spec:
                    tool_names.append(tool_spec["name"])
                elif hasattr(tool_spec, "function") and hasattr(
                    tool_spec.function, "name"
                ):
                    tool_names.append(tool_spec.function.name)
                else:
                    # Fallback: convert to string and try to extract name
                    tool_names.append(str(tool_spec))

            return tool_names
        except Exception as e:
            log_exception(logger, "error_getting_tool_names", e)
            return []

    def get_tool_details(self) -> List[Dict[str, Any]]:
        """
        Get detailed information about all loaded tools.

        Returns:
            List[Dict[str, Any]]: List of tool detail dictionaries with:
                - name: Tool name
                - description: Tool description
                - source_type: Type of tool source (python, mcp, a2a)
                - source_id: Identifier for the tool source
        """
        try:
            tool_details = []

            # Get tool specs from strands Agent's tool_registry (authoritative source)
            # AgentProxy is a full proxy - we can call methods directly without context manager
            tool_spec_map = {}
            try:
                tool_specs_list = self.agent_proxy.tool_registry.get_all_tool_specs()
                tool_spec_map = {spec.get("name"): spec for spec in tool_specs_list}
                logger.debug(
                    "loaded_tool_specs_from_registry", count=len(tool_spec_map)
                )
            except Exception as e:
                logger.debug("could_not_load_tool_specs_from_registry", error=str(e))

            # Get enhanced tool specs from agent proxy
            enhanced_specs = getattr(self.agent_proxy, "tool_specs", [])

            if not enhanced_specs:
                return []

            # Process each enhanced tool spec
            for spec in enhanced_specs:
                if not isinstance(spec, dict):
                    continue

                # Get source info
                source_type = spec.get("type", "unknown")
                source_id = spec.get("id", "unknown")

                # Get tool_names - this is the authoritative list
                tool_names = spec.get("tool_names", [])

                # Get the actual tool objects (may be None or contain modules/functions)
                tools = spec.get("tools")

                # Try to match tool_names with tool objects for descriptions
                if tools and len(tools) == len(tool_names):
                    # We have matching tool objects - extract details
                    for name, tool in zip(tool_names, tools):
                        tool_info = self._extract_tool_info_with_name(
                            name, tool, source_type, source_id, tool_spec_map
                        )
                        tool_details.append(tool_info)
                else:
                    # Fall back to just using tool_names
                    for name in tool_names:
                        # Still try to get description from tool_spec_map
                        description = "No description available"
                        if name in tool_spec_map:
                            desc = tool_spec_map[name].get("description")
                            if desc:
                                description = desc

                        tool_details.append(
                            {
                                "name": name,
                                "description": description,
                                "source_type": source_type,
                                "source_id": source_id,
                            }
                        )

            return tool_details

        except Exception as e:
            log_exception(logger, "error_getting_tool_details", e)
            return []

    def _extract_tool_info_with_name(
        self,
        name: str,
        tool: Any,
        source_type: str,
        source_id: str,
        tool_spec_map: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Extract information from a tool object, using the provided name as authoritative.

        Args:
            name: The authoritative tool name from tool_names
            tool: Tool object (could be function, module, or other)
            source_type: Type of tool source
            source_id: Identifier for tool source
            tool_spec_map: Map of tool names to ToolSpec dicts from strands registry

        Returns:
            Dictionary with tool info
        """
        try:
            description = "No description available"

            # First priority: Get description from strands tool registry (ToolSpec)
            if name in tool_spec_map:
                desc = tool_spec_map[name].get("description")
                if desc:
                    description = desc
                    return {
                        "name": name,
                        "description": description,
                        "source_type": source_type,
                        "source_id": source_id,
                    }

            # Fallback: Check for MCP tool with tool_spec (JSON Schema document)
            if hasattr(tool, "tool_spec"):
                tool_spec = tool.tool_spec
                # tool_spec is a dict/JSON Schema with a top-level description field
                if isinstance(tool_spec, dict) and "description" in tool_spec:
                    desc = tool_spec["description"]
                    if desc:
                        description = desc
                # Fallback: check if it's an object with description attribute
                elif hasattr(tool_spec, "description") and tool_spec.description:
                    description = tool_spec.description

            # If tool is a module, try to get the function from it
            elif isinstance(tool, types.ModuleType):
                # Try to get a function with the same name from the module
                if hasattr(tool, name):
                    func = getattr(tool, name)
                    if callable(func) and hasattr(func, "__doc__") and func.__doc__:
                        description = func.__doc__.strip().split("\n")[0]
                else:
                    # Try to get module docstring
                    if hasattr(tool, "__doc__") and tool.__doc__:
                        description = tool.__doc__.strip().split("\n")[0]

            # If tool is a callable, get its docstring
            elif callable(tool):
                if hasattr(tool, "__doc__") and tool.__doc__:
                    description = tool.__doc__.strip().split("\n")[0]

            # If tool has explicit name and description attributes
            elif hasattr(tool, "name") and hasattr(tool, "description"):
                if tool.description:
                    description = tool.description

            # If tool has a function attribute
            elif hasattr(tool, "function"):
                func = tool.function
                if hasattr(func, "__doc__") and func.__doc__:
                    description = func.__doc__.strip().split("\n")[0]

            # If tool is a dict
            elif isinstance(tool, dict):
                description = tool.get("description", description)

            return {
                "name": name,
                "description": description,
                "source_type": source_type,
                "source_id": source_id,
            }

        except Exception as e:
            logger.debug("error_extracting_tool_info", error=str(e))
            return {
                "name": name,
                "description": "No description available",
                "source_type": source_type,
                "source_id": source_id,
            }

    def get_conversation_stats(self) -> Dict[str, int]:
        """
        Get conversation statistics.

        Returns:
            Dict[str, int]: Statistics about the conversation
        """
        try:
            # Get tool count
            tool_names = self.get_tool_names()
            tool_count = len(tool_names)

            # Try to get message count - AgentProxy proxies the messages attribute
            message_count = 0
            try:
                messages = self.agent_proxy.messages
                message_count = len(messages) if messages else 0
            except Exception as e:
                logger.debug("could_not_access_messages", error=str(e))

            return {"message_count": message_count, "tool_count": tool_count}
        except Exception as e:
            log_exception(logger, "error_getting_conversation_stats", e)
            return {"message_count": 0, "tool_count": 0}
