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
from typing import List, Dict, Any, Optional, TextIO
import litellm

from strands import Agent
from content_processor import parse_input_with_files

def print_welcome_message():
    """Prints the initial welcome message and instructions to stdout."""
    print("Welcome to Yet Another ChatBot Agent!")
    print("Type 'exit' or 'quit' on a line by itself to end the conversation.")
    print("Use Alt+Enter to add a new line. Use CTRL-D or CTRL-C to exit.")
    print("To upload a file in-chat, use the format: file('path/to/file.ext')")
    print("Pro-tip: Type \"file('\" and then press Tab for path auto-completion.")

def print_startup_info(
    model_id: str,
    system_prompt: str,
    prompt_source: str,
    tool_configs: List[Dict[str, Any]],
    startup_files: List[tuple[str, str]],
    output_file: TextIO = sys.stdout
):
    """Prints a summary of the configuration to a specified output stream."""
    def write(msg):
        print(msg, file=output_file)

    write("-" * 20)
    first_line = system_prompt.split('\n')[0]
    ellipsis = "..." if '\n' in system_prompt else ""
    write(f"System Prompt (from {prompt_source}): \"{first_line}{ellipsis}\"")
    write(f"Model: {model_id}")
    
    if tool_configs:
        write("Available Tools:")
        for config in tool_configs:
            tool_type = config.get('type', 'unknown')
            write(f"  - {config.get('id', 'unknown')} (type: {tool_type}, from {config.get('source_file', 'N/A')})")
    else:
        write("Available Tools: None")

    if startup_files:
        write(f"Uploaded Files ({len(startup_files)}):")
        for path, media_type in startup_files:
            write(f"  - {path} ({media_type})")
    else:
        write("Uploaded Files: None")
    write("-" * 20)


class CustomPathCompleter(Completer):
    """
    A completer that provides path suggestions only when the cursor is inside
    a file('...') or file("...") call, after an opening quote is typed.
    """
    path_completer = PathCompleter()
    def get_completions(self, document: Document, complete_event):
        match = re.search(r"file\((['\"])([^'\"]*)$", document.text_before_cursor)
        if match:
            path_prefix = match.group(2)
            path_doc = Document(text=path_prefix, cursor_position=len(path_prefix))
            for comp in self.path_completer.get_completions(path_doc, complete_event):
                yield comp


async def _handle_agent_stream(agent: Agent, message: str):
    """
    Drives the agent's streaming response and handles potential errors.
    The actual printing is done by the callback handler.
    """
    agent_input = parse_input_with_files(message)
    try:
        # This loop drives the streaming process. We simply consume the generator
        # to trigger the callback handler for each event.
        async for _ in agent.stream_async(agent_input):
            pass
    except litellm.ServiceUnavailableError as e:
        logger.warning(f"A model provider error occurred: {e}")
        print("\nSorry, the model's response was interrupted. This can happen with complex requests.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during streaming: {e}")
        print("\nSorry, an unexpected error occurred while generating the response.")


async def run_headless_mode(agent: Agent, message: str):
    """Runs the chatbot non-interactively for scripting."""
    await _handle_agent_stream(agent, message)


async def chat_loop_async(agent: Agent, initial_message: Optional[str] = None):
    """Runs the main interactive conversation loop using prompt_toolkit."""
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
        await _handle_agent_stream(agent, initial_message)

    while True:
        try:
            user_input = await session.prompt_async("You: ", multiline=True, key_bindings=bindings)
            if user_input.strip().lower() in ["exit", "quit"]:
                break
            if not user_input.strip():
                continue
            await _handle_agent_stream(agent, user_input)
        except (KeyboardInterrupt, EOFError):
            print()
            break