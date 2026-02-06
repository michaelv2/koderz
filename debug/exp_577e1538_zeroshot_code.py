from typing import List, Tuple

def find_closest_elements(numbers: List[float]) -> Tuple[float, float]:
    """ From a supplied list of numbers (of length at least two) select and return two that are the closest to each
    other and return them in order (smaller number, larger number).
    >>> find_closest_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.2])
    (2.0, 2.2)
    >>> find_closest_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.0])
    (2.0, 2.0)
    """
    if len(numbers) < 2:
        raise ValueError("At least two numbers are required")

    nums = sorted(numbers)
    best_a, best_b = nums[0], nums[1]
    best_diff = best_b - best_a

    for i in range(1, len(nums) - 1):
        a, b = nums[i], nums[i + 1]
        diff = b - a
        if diff < best_diff:
            best_diff = diff
            best_a, best_b = a, b

    return (best_a, best_b)