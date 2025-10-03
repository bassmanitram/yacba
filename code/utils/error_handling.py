"""
Error handling and formatting for YACBA CLI.

Provides consistent error formatting and agent interaction error handling.
"""

def format_error(e: Exception) -> str:
    """
    Extracts detailed information from exceptions for better user feedback.

    Args:
        e: Exception to format

    Returns:
        Formatted error message with details
    """
    details = f"Error Type: {type(e).__name__}"
    message = getattr(e, "message", None)
    if message:
        details += f"\nMessage: {message}"

    response = getattr(e, "response", None)
    if response and hasattr(response, "text"):
        details += f"\nOriginal Response: {response.text}"

    return str(e)
