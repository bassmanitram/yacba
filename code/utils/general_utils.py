from typing import Any, Dict


def clean_dict(d: Dict[str, Any]) -> Dict[str, Any]:
	"""
	Clean a dict of None values (shallow)
	"""
	return {k: v for k, v in d.items() if v is not None}