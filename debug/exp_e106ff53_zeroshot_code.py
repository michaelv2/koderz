from typing import List

def rescale_to_unit(numbers: List[float]) -> List[float]:
    min_value = min(numbers)
    max_value = max(numbers)
    range_value = max_value - min_value
    return [(num - min_value) / range_value for num in numbers]