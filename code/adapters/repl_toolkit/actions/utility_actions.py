"""
Utility actions for YACBA CLI.

Handles utility actions:
- /echo: Echo text directly to stdout (bypassing printer)
"""

import sys
from repl_toolkit import Action, ActionContext, ActionRegistry


def handle_echo(context: ActionContext) -> None:
    """
    Echo the rest of the line directly to stdout.
    
    This action ALWAYS writes to sys.stdout, bypassing the configured printer.
    This is useful for synchronization markers when running YACBA from a FIFO,
    allowing post-processing to detect lifecycle points in the output stream.
    
    Args:
        context: Action context containing the arguments to echo
    """
    # Get the text after /echo command
    # user_input contains the full line, we need to strip the /echo part
    if context.user_input:
        # Remove the /echo command and any leading whitespace
        text = context.user_input.replace('/echo', '', 1).lstrip()
    else:
        # Fallback to args if user_input not available
        text = ' '.join(context.args) if context.args else ''
    
    # Write directly to stdout, bypassing the printer
    print(text, file=sys.stdout, flush=True)


def register_utility_actions(registry: ActionRegistry) -> None:
    """Register utility actions."""

    echo_action = Action(
        name="echo",
        command="/echo",
        handler=handle_echo,
        category="Utility",
        description="Echo text directly to stdout",
        command_usage="/echo <text> - Echo text to stdout (bypassing printer, useful for FIFO synchronization)",
    )

    registry.register_action(echo_action)
