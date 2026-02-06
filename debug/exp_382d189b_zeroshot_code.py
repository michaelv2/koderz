from typing import List, Any

def filter_integers(values: List[Any]) -> List[int]:
    return [v for v in values if type(v) is int]