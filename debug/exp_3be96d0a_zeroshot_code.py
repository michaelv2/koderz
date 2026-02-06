from typing import List, Tuple

def rolling_max(numbers):
    """From a given list of integers, generate a list of rolling maximum elements found up to each position."""
    result = []
    current_max = None
    for n in numbers:
        if current_max is None or n > current_max:
            current_max = n
        result.append(current_max)
    return result