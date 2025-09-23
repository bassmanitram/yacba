from typing import Any


def recursively_remove(obj: Any, prop: str) -> None:
    """
    Recursively traverses a dictionary or list and removes all keys
    named 'additionalProperties'. This is a workaround for APIs
    like Google's that don't support this standard JSON Schema key.
    
    Args:
        obj: Object to clean (modified in place)
    """
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            if key == prop:
                del obj[key]
            else:
                recursively_remove(obj[key])
    elif isinstance(obj, list):
        for item in obj:
            recursively_remove(item)