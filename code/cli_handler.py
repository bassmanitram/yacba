# cli_handler.py
# Handles all command-line interface interactions for the chatbot.

import asyncio
import re
import sys
import json
from typing import List, Dict, Any, Optional, TextIO, Union

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, PathCompleter, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from loguru import logger

from strands import Agent
from content_processor import parse_input_with_files
from yacba_manager import ChatbotManager
from framework_adapters import FrameworkAdapter


def print_welcome_message():
    """Prints the initial welcome message and instructions to stdout."""
    print("Welcome to Yet Another ChatBot Agent!")
    print("Type 'exit' or 'quit' to end. Type /help for a list of commands.")
    print("Use Alt+Enter for a new line. Use CTRL-D or CTRL-C to exit.")
    print("To upload a file in-chat, use the format: file('path/to/file.ext')")


def print_startup_info(
    model_id: str,
    system_prompt: str,
    prompt_source: str,
    loaded_tools: List[Any],
    startup_files: List[tuple[str, str]],
    output_file: TextIO = sys.stdout,
):
    """Prints a summary of the configuration to a specified output stream."""

    def write(msg):
        print(msg, file=output_file)

    write("-" * 20)
    first_line = system_prompt.split("\n")[0]
    ellipsis = "..." if "\n" in system_prompt else ""
    write(f'System Prompt (from {prompt_source}): "{first_line}{ellipsis}"')
    write(f"Model: {model_id}")

    if loaded_tools:
        write("Available Tools:")
        for tool in loaded_tools:
            try:
                # All valid strands tools have a .tool_spec attribute
                tool_name = tool.tool_spec.get("name", "unnamed-tool")
                write(f"  - {tool_name}")
            except AttributeError:
                write(f"  - (Unnamed or invalid tool object: {type(tool)})")
    else:
        write("Available Tools: None")

    if startup_files:
        write(f"Uploaded Files ({len(startup_files)}):")
        for path, media_type in startup_files:
            write(f"  - {path} ({media_type})")
    else:
        write("Uploaded Files: None")
    write("-" * 20)


class YacbaCompleter(Completer):
    """
    A context-aware completer that switches between meta-command and path completion.
    """
    path_completer = PathCompleter()
    meta_commands = [
        "/help",
        "/save",
        "/clear",
        "/history",
        "/tools",
        "/exit",
        "/quit",
    ]

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor
        
        # Check for in-chat file upload syntax
        file_match = re.search(r"file\((['\"])(.*?)$", text)
        if file_match:
            path_prefix = file_match.group(2)
            if file_match.group(1) in path_prefix:
                 return

            path_doc = Document(text=path_prefix, cursor_position=len(path_prefix))
            for comp in self.path_completer.get_completions(path_doc, complete_event):
                yield comp
            return

        # Check for meta-command syntax
        if text.startswith("/") and " " not in text:
            for command in self.meta_commands:
                if command.startswith(text):
                    yield Completion(
                        command,
                        start_position=-len(text),
                        display=command,
                        display_meta=f"meta-command",
                    )


def _format_error(e: Exception) -> str:
    """Extracts detailed information from exceptions for better user feedback."""
    details = f"Error Type: {type(e).__name__}"
    message = getattr(e, "message", None)
    if message:
        details += f"\nMessage: {message}"
    
    response = getattr(e, "response", None)
    if response and hasattr(response, "text"):
        details += f"\nOriginal Response: {response.text}"
        
    return str(e)


class CommandHandler:
    """Handles meta-commands using a registry pattern."""
    def __init__(self, manager: ChatbotManager):
        self.manager = manager
        self._commands = {
            "/help": self._show_help,
            "/save": self._save_session,
            "/clear": self._clear_session,
            "/history": self._show_history,
            "/tools": self._list_tools,
        }

    async def handle(self, user_input: str):
        """Parses and executes a meta-command."""
        parts = user_input.split()
        command = parts[0]
        args = parts[1:]

        handler_func = self._commands.get(command)
        if handler_func:
            await handler_func(args)
        else:
            print(f"Unknown command: {command}. Type /help for a list of commands.")

    async def _show_help(self, args: List[str]):
        print("Available commands:")
        print("  /help           - Show this help message.")
        print("  /save [name]    - Save the session. If name is provided, switches to that session.")
        print("  /clear          - Clear the current conversation history and session file.")
        print("  /history        - Print the current message history.")
        print("  /tools          - List the currently loaded tools.")
        print("  /exit, /quit    - Exit the application.")

# Inside the CommandHandler class in cli_handler.py

    async def _save_session(self, args: List[str]):
        """Handles the /save command, switching sessions if a name is provided."""
        if args:
            session_name = args[0]
            # This is the key action: tell the delegating proxy to switch its target.
            # We now pass the agent instance to facilitate a proper state sync.
            if self.manager.engine and self.manager.engine.agent:
                self.manager.session_manager.set_active_session(session_name)
            else:
                print("Error: Agent is not available to switch session.", file=sys.stderr)
                return
        
        # Trigger a manual save for immediate user feedback.
        self.manager.save_session()

    async def _clear_session(self, args: List[str]):
        self.manager.clear_session()

    async def _show_history(self, args: List[str]):
        if self.manager.engine and self.manager.engine.agent:
            print(json.dumps(self.manager.engine.agent.messages, indent=2))

    async def _list_tools(self, args: List[str]):
        if self.manager.engine and self.manager.engine.loaded_tools:
            print("Loaded tools:")
            for tool in self.manager.engine.loaded_tools:
                if hasattr(tool, "tool_spec"):
                    print(f"  - {tool.tool_spec.get('name', 'unnamed-tool')}")
                else:
                    print(f"  - (Unnamed or invalid tool object: {type(tool)})")
        else:
            print("No tools are currently loaded.")


async def _handle_agent_stream(
    agent: Agent,
    message: Union[str, List[Dict[str, Any]]],
    adapter: FrameworkAdapter,
) -> bool:
    """
    Drives the agent's streaming response and handles potential errors.
    Returns True on success, False on failure.
    """
    if not message:
        return True

    exceptions_to_catch = adapter.expected_exceptions if adapter else (Exception,)

    try:
        transformed_message = adapter.transform_content(message)
        async for _ in agent.stream_async(transformed_message):
            pass
        return True
    except exceptions_to_catch as e:
        error_details = _format_error(e)
        print(
            f"\nA model provider error occurred:\n{error_details}", file=sys.stderr
        )
        return False
    except Exception as e:
        print(
            f"\nAn unexpected error occurred while generating the response: {e}",
            file=sys.stderr,
        )
        return False


async def run_headless_mode(manager: ChatbotManager, message: str) -> bool:
    """Runs the chatbot non-interactively for scripting. Returns success status."""
    if not manager.engine or not manager.engine.agent or not manager.engine.framework_adapter:
        return False
    
    agent_input = parse_input_with_files(message, manager.config.max_files)
    
    return await _handle_agent_stream(manager.engine.agent, agent_input, manager.engine.framework_adapter)


async def chat_loop_async(
    manager: ChatbotManager,
    initial_message: Optional[str] = None,
    max_files: int = 20,
):
    """Runs the main interactive conversation loop using prompt_toolkit."""
    engine = manager.engine
    if not engine or not engine.agent or not engine.framework_adapter:
        logger.error("Cannot start chat loop: engine or agent not initialized.")
        return

    history = FileHistory(".yacba_history")
    session = PromptSession(history=history, completer=YacbaCompleter())
    command_handler = CommandHandler(manager)
    bindings = KeyBindings()

    @bindings.add("enter")
    def _(event):
        event.app.current_buffer.validate_and_handle()

    @bindings.add("escape", "enter")
    def _(event):
        event.app.current_buffer.insert_text("\n")

    if initial_message:
        print(f"You: {initial_message}")
        agent_input = parse_input_with_files(initial_message, max_files)
        await _handle_agent_stream(engine.agent, agent_input, engine.framework_adapter)

    while True:
        try:
            user_input = await session.prompt_async(
                "You: ", multiline=True, key_bindings=bindings
            )
            if user_input.strip().lower() in ["/exit", "/quit", "exit", "quit"]:
                break
            if not user_input.strip():
                continue
            
            if user_input.strip().startswith("/"):
                await command_handler.handle(user_input.strip())
                continue

            agent_input = parse_input_with_files(user_input, max_files)
            await _handle_agent_stream(engine.agent, agent_input, engine.framework_adapter)

        except (KeyboardInterrupt, EOFError):
            print()
            break
