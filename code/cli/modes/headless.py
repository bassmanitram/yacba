"""
Headless mode for YACBA CLI.

Handles non-interactive execution for scripting and automation.
"""

from yacba_types.backend import ChatBackend

async def run_headless_mode(backend: ChatBackend, message: str) -> bool:
    """
    Runs the chatbot non-interactively for scripting.
    
    Args:
        manager: ChatbotManager instance
        message: Message to process
        
    Returns:
        Success status
    """

    return await backend.handle_input(message)
