from typing import List, Any

def filter_integers(values: List[Any]) -> List[int]:
    result = []
    for value in values:
        if isinstance(value, int):
            result.append(value)
    return result