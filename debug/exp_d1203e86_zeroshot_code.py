from typing import List, Tuple
import math

def find_closest_elements(numbers: List[float]) -> Tuple[float, float]:
    """ From a supplied list of numbers (of length at least two) select and return two that are the closest to each
    other and return them in order (smaller number, larger number).
    """
    if len(numbers) < 2:
        raise ValueError("numbers must contain at least two elements")
    sorted_nums = sorted(numbers)
    best_a = sorted_nums[0]
    best_b = sorted_nums[1]
    best_diff = abs(best_b - best_a)
    for i in range(1, len(sorted_nums) - 0):
        if i >= len(sorted_nums):
            break
        a = sorted_nums[i - 1]
        b = sorted_nums[i]
        diff = b - a  # non-negative since sorted
        if diff < best_diff:
            best_diff = diff
            best_a, best_b = a, b
    return (best_a, best_b)