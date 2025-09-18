# cli_handler.py
# Handles all command-line interface interactions for the chatbot.

import asyncio
import re
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import PathCompleter, Completer
from prompt_toolkit.document import Document
from loguru import logger
from typing import List, Dict, Any, Optional, TextIO, Union
import litellm

from strands import Agent
from content_processor import parse_input_with_files
from framework_adapters import FrameworkAdapter

def print_welcome_message():
    # ... (function is unchanged)
    print("Welcome to Yet Another ChatBot Agent!")
    print("Type 'exit' or 'quit' on a line by itself to end the conversation.")
    print("Use Alt+Enter to add a new line. Use CTRL-D or CTRL-C to exit.")
    print("To upload a file in-chat, use the format: file('path/to/file.ext')")
    print("Pro-tip: Type \"file('\" and then press Tab for path auto-completion.")

def print_startup_info(model_id: str, system_prompt: str, prompt_source: str, loaded_tools: List[Any], startup_files: List[List[str]], output_file: TextIO = sys.stdout):
    # ... (function is unchanged)
    def write(msg):
        print(msg, file=output_file)

    write("-" * 20)
    first_line = system_prompt.split('\n')[0]
    ellipsis = "..." if '\n' in system_prompt else ""
    write(f"System Prompt (from {prompt_source}): \"{first_line}{ellipsis}\"")
    write(f"Model: {model_id}")
    
    if loaded_tools:
        write("Available Tools:")
        for tool in loaded_tools:
            try:
                tool_name = tool.tool_spec.get('name', 'unnamed-tool')
                write(f"  - {tool_name}")
            except AttributeError:
                write(f"  - (Unnamed or invalid tool object: {type(tool)})")
    else:
        write("Available Tools: None")

    if startup_files:
        write(f"Uploaded Files ({len(startup_files)}):")
        for file_arg in startup_files:
            write(f"  - {file_arg[0]}")
    else:
        write("Uploaded Files: None")
    write("-" * 20)

class CustomPathCompleter(Completer):
    # ... (class is unchanged)
    path_completer = PathCompleter()
    def get_completions(self, document: Document, complete_event):
        match = re.search(r"file\((['\"])([^'\"]*)$", document.text_before_cursor)
        if match:
            path_prefix = match.group(2)
            path_doc = Document(text=path_prefix, cursor_position=len(path_prefix))
            for comp in self.path_completer.get_completions(path_doc, complete_event):
                yield comp

def _format_litellm_error(e: Exception) -> str:
    # ... (function is unchanged)
    details = f"Error Type: {type(e).__name__}"
    if hasattr(e, 'message'):
        details += f"\nMessage: {e.message}"
    if hasattr(e, 'response') and hasattr(e.response, 'text'):
        details += f"\nOriginal Response: {e.response.text}"
    return details

async def _handle_agent_stream(agent: Agent, message: Union[str, Dict[str, Any]]) -> bool:
    # ... (function is unchanged)
    try:
        async for _ in agent.stream_async(message):
            pass
        return True
    except (litellm.exceptions.APIConnectionError, litellm.exceptions.ServiceUnavailableError) as e:
        error_details = _format_litellm_error(e)
        print(f"\nSorry, a model provider error occurred:\n{error_details}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"\nSorry, an unexpected error occurred while generating the response: {e}", file=sys.stderr)
        return False

async def run_headless_mode(agent: Agent, adapter: FrameworkAdapter, message: str) -> bool:
    """Runs the chatbot non-interactively for scripting."""
    agent_input = parse_input_with_files(message)
    if isinstance(agent_input, list):
        final_content = adapter.adapt_content(agent_input)
        # Wrap the content in the standard message format for the agent
        agent_input = {"role": "user", "content": final_content}
        
    return await _handle_agent_stream(agent, agent_input)

async def chat_loop_async(agent: Agent, adapter: FrameworkAdapter, initial_message: Optional[str] = None, max_files: int = 20):
    """Runs the main interactive conversation loop."""
    history = FileHistory(".chatbot_history")
    session = PromptSession(history=history, completer=CustomPathCompleter())
    bindings = KeyBindings()

    @bindings.add('enter')
    def _(event):
        event.app.current_buffer.validate_and_handle()

    @bindings.add('escape', 'enter')
    def _(event):
        event.app.current_buffer.insert_text('\n')
        
    if initial_message:
        print(f"You: {initial_message}")
        agent_input = parse_input_with_files(initial_message, max_files)
        if isinstance(agent_input, list):
            agent_input = adapter.adapt_content(agent_input)
        await _handle_agent_stream(agent, agent_input)

    while True:
        try:
            user_input = await session.prompt_async("You: ", multiline=True, key_bindings=bindings)
            if user_input.strip().lower() in ["exit", "quit"]:
                break
            if not user_input.strip():
                continue
            
            agent_input = parse_input_with_files(user_input, max_files)
            if isinstance(agent_input, list):
                agent_input = adapter.adapt_content(agent_input)
                
            await _handle_agent_stream(agent, agent_input)
        except (KeyboardInterrupt, EOFError):
            print()
            break
