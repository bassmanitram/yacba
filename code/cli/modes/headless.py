"""
Headless mode for YACBA CLI.

Handles non-interactive execution for scripting and automation.

Headless mode can be used "interactively" too - just use the /send
command on a line by itself and the existing buffer will be sent to
the LLM, and its response awaited (which will be sent to stdout) before
stdin is again read. 
"""

import asyncio
import readline
from sys import stderr

from loguru import logger
from yacba_types.backend import ChatBackend

async def run_headless_mode(backend: ChatBackend, initial_message: str = None, verbose: bool = True) -> bool:
    """
    Runs YACBA in a multi-turn headless mode.
    It reads stdin, buffers input, sends to the backend upon '/send' or EOF,
    streams output to stdout, and then resumes reading (unless it reached EOF)

    Consider it a bare-bones alternative to "interactive"
    """
    
    # 1. Handle initial message if provided
    if initial_message:
        if verbose:
            print("[Sending initial prompt]", file=stderr)
        await backend.handle_input(initial_message)
        if verbose:
            print("[End of initial response]", file=stderr)
        print("")

        if verbose:
            print("\n[YACBA Headless Interactive Mode]", file=stderr)
            print("Type your message. Use '/send' on a new line to send, or Ctrl+D (EOF) to exit.", file=stderr)

    should_exit_program = False
    while not should_exit_program:
        current_input_buffer = []
        is_eof_this_turn = False
        
        while True:
            # 2. Asynchronously read a line from stdin
            # readline() is blocking, so we run it in a separate thread
            try:
                line = await asyncio.to_thread(input)
            except EOFError:
                if verbose:
                    print("[EOF received]", file=stderr)
                is_eof_this_turn = True
                should_exit_program = True # Signal outer loop to exit after this turn
                break
            
            except Exception as e:
                logger.error(f"Error reading stdin: {e}", file=stderr)
                should_exit_program = True
                break # Break inner loop, will lead to outer loop exit
                       
            if line.strip() == "/send":
                if verbose:
                    print("[/send command received]", file=stderr)
                break # '/send' command received, process buffer
            
            if line.strip() == "/clear":
                if verbose:
                    print("[/clear command received]", file=stderr)
                backend.session_manager.clear()
                break # '/clear' command received, clear the context
            
            current_input_buffer.append(line)
            # Optional: provide user feedback by echoing input to stderr
            # print(f"> {line.strip()}", file=stderr) 

        user_input = "".join(current_input_buffer).strip()

        # 3. Send buffer to backend if there's content
        if user_input:
            if verbose:
                print(f"\n[Sending message to agent...]", file=stderr)
            await backend.handle_input(user_input)
            print("")
            if verbose:
                print("[Agent response completed.]", file=stderr)
        elif is_eof_this_turn:
            # Nothing in buffer, and EOF was hit. Just proceed to exit.
            pass
        else:
            # `/send` was typed but buffer was empty (or only whitespace).
            if verbose:
                print("[No content to send. Waiting for next input.]", file=stderr)

        if should_exit_program:
            break # Exit the main program loop

    if verbose:
        print("\n[YACBA Headless Interactive Mode Exited]", file=stderr)

