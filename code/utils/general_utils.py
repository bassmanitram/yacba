from datetime import datetime
from typing import Any, Dict

MAX_BYTES_LENGTH_FOR_DISPLAY = 50
ELLIPSIS = "..."
REAL_LENGTH = MAX_BYTES_LENGTH_FOR_DISPLAY - len(ELLIPSIS)


def clean_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean a dict of None values (shallow)
    """
    return {k: v for k, v in d.items() if v is not None}


def custom_json_serializer_for_display(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, bytes):
        s = obj.decode("utf-8", errors="ignore")
        if len(s) <= MAX_BYTES_LENGTH_FOR_DISPLAY:
            return s
        return s[:REAL_LENGTH] + ELLIPSIS

    # Let the default encoder handle other types or raise TypeError
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
