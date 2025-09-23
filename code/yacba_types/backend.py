from typing import AsyncIterator, Protocol, Optional, List, Any

class ChatBackend(Protocol):
    async def stream_response(
        self,
        message: str,
        files: Optional[List[Any]] = None
    ) -> AsyncIterator[str]:
        """
        Asynchronously yields response chunks for a given message and optional files.
        """
        ...