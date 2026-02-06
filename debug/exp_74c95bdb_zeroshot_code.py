from typing import List

def rescale_to_unit(numbers: List[float]) -> List[float]:
    """Given a list of numbers, apply a linear transform so that the
    smallest value maps to 0.0 and the largest maps to 1.0.
    If all numbers are equal, return zeros of the same length."""
    if not numbers:
        return []
    mn, mx = min(numbers), max(numbers)
    diff = mx - mn
    if diff == 0:
        return [0.0 for _ in numbers]
    scale = 1.0 / diff
    return [(x - mn) * scale for x in numbers]