from typing import Any, Dict


def clean_dict(d: Dict[str, Any]) -> Dict[str, Any]:
	"""
	Clean a dict of None values (shallow)
	"""
	return {k: v for k, v in d.items() if v is not None}

import collections.abc
from typing import Any

def print_structured_data(data: Any, indent_level: int = 0, initial_max_len: int = 90, printer = print):
    """
	Prints structured data (dict, list, scalar), applying specific formatting rules:
    - If data is a dictionary, its keys are sorted alphabetically.
    - Property name and value are printed, separated by ":".
    - If a value is an 'elementary' type (int, float, bool, or None), it's printed
      as its string representation, with NO truncation.
    - If a value is another dictionary, it recurses and indents.
    - Other values (strings, lists, custom objects, etc.) are converted to string.
    - String values (including converted ones) are truncated if their length
      exceeds an effective maximum length.
    - The effective maximum length reduces with deeper indentation levels.
    - If initial_max_len is -1, no truncation occurs for any string/non-elementary type.
    - If the top-level 'data' itself is not a dictionary, it's printed directly
      according to the value rules (no key: prefix).

    Args:
        data (Any): The data to be printed. Can be a dict, string, int, list, None, etc.
        indent_level (int): The current indentation level (for internal recursion).
        initial_max_len (int): The maximum length for string truncation at the
                                top-level. Set to -1 for no truncation.
                                This length is reduced for deeper indent levels.
    """
    indent_str = "  " * indent_level

    # Determine effective maximum length for truncation
    if initial_max_len == -1:
        effective_max_len = float('inf')  # No truncation
    else:
        # Reduce effective max length for truncation as indentation increases.
        # Ensures at least 6 chars for "abc..." to accommodate truncation ellipsis.
        effective_max_len = max(6, initial_max_len - (indent_level * 8))

    def _format_and_print_value(value_to_format: Any, prefix: str = ""):
        """Helper to format and print a value based on rules."""
        if value_to_format is None:
            printer(f"{indent_str}{prefix}None")
        elif isinstance(value_to_format, (int, float, bool)):
            # Elementary types (int, float, bool) are printed without truncation
            printer(f"{indent_str}{prefix}{str(value_to_format)}")
        elif isinstance(value_to_format, collections.abc.Mapping):
            printer(f"{indent_str}{prefix}") # Print key then recurse on next line
            print_structured_data(value_to_format, indent_level + 1, initial_max_len)
        else: # Handle all other types (strings, lists, objects, etc.) with potential truncation
            value_as_str = str(value_to_format)
            display_value = value_as_str
            # Apply truncation only if effective_max_len is not infinite
            if effective_max_len != float('inf') and len(value_as_str) > effective_max_len:
                display_value = value_as_str[:effective_max_len - 3] + "..."
            printer(f"{indent_str}{prefix}{display_value}")

    if isinstance(data, collections.abc.Mapping):
        # Top-level 'data' is a dictionary, iterate through its sorted properties
        for key, value in sorted(data.items()):
            key_name = str(key)
            _format_and_print_value(value, prefix=f"{key_name}: ")
    else:
        # Top-level 'data' is not a dictionary. Apply value rules directly without a key prefix.
        _format_and_print_value(data)

