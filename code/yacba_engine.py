import os
from typing import List, Dict, Any, Optional, Tuple, AsyncIterator
from contextlib import ExitStack
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger

from strands import Agent
from strands.session.session_manager import SessionManager
from adapters.tools.factory import ToolFactory
from yacba_types.models import FrameworkAdapter
from delegating_session import DelegatingSession
from model_loader import StrandsModelLoader
from yacba_config import YacbaConfig
from yacba_types.tools import ToolProcessingResult, ToolSystemStatus
from yacba_types.backend import ChatBackend

class YacbaEngine(ChatBackend):
    def __init__(self, config: YacbaConfig):
        self.config = config
        self.agent: Optional[Agent] = None
        self.framework_adapter: Optional[FrameworkAdapter] = None
        self.session_manager: Optional[SessionManager] = None
        self.tool_factory: Optional[ToolFactory] = None
        self.model_loader: Optional[StrandsModelLoader] = None
        self.is_ready: bool = False

    def startup(self) -> bool:
        # ...existing startup logic...
        # Initialize agent, framework_adapter, etc.
        self.is_ready = True  # Set to True if startup succeeds
        return self.is_ready

    def shutdown(self) -> None:
        # ...existing shutdown logic...
        self.is_ready = False

    async def stream_response(
        self,
        message: str,
        files: Optional[List[Any]] = None
    ) -> AsyncIterator[str]:
        """
        Asynchronously yields response chunks for a given message and optional files.
        """
        if not self.agent or not self.framework_adapter:
            logger.error("Engine not initialized: agent or framework_adapter missing.")
            return
        agent_input = self.prepare_input(message, files)
        async for chunk in self.framework_adapter.stream(self.agent, agent_input):
            yield chunk

    def prepare_input(self, message: str, files: Optional[List[Any]] = None) -> Any:
        # ...existing logic to prepare agent input from message and files...
        return {
            "message": message,
            "files": files or []
        }