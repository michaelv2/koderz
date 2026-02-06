from typing import List

def rescale_to_unit(numbers: List[float]) -> List[float]:
    lo = min(numbers)
    hi = max(numbers)
    if hi == lo:
        return [0.0 for _ in numbers]
    inv_range = 1.0 / (hi - lo)
    return [(x - lo) * inv_range for x in numbers]