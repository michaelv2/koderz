from typing import List, Any

def filter_integers(values: List[Any]) -> List[int]:
    """Return a list containing only the integer values from the input, preserving order."""
    return [v for v in values if isinstance(v, int)]