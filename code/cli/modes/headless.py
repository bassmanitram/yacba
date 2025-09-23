"""
Headless mode for YACBA CLI.

Handles non-interactive execution for scripting and automation.
"""

from yacba_manager import ChatbotManager
from content_processor import parse_input_with_files
from ..interface import handle_agent_stream


async def run_headless_mode(manager: ChatbotManager, message: str) -> bool:
    """
    Runs the chatbot non-interactively for scripting.
    
    Args:
        manager: ChatbotManager instance
        message: Message to process
        
    Returns:
        Success status
    """
    if not manager.engine or not manager.engine.agent or not manager.engine.framework_adapter:
        return False
    
    agent_input = parse_input_with_files(message, manager.config.max_files)
    
    return await handle_agent_stream(
        manager.engine.agent, 
        agent_input, 
        manager.engine.framework_adapter
    )
