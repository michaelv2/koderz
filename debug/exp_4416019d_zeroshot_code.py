from typing import List, Tuple

def find_closest_elements(numbers: List[float]) -> Tuple[float, float]:
    if len(numbers) < 2:
        raise ValueError("At least two numbers are required.")
    nums_sorted = sorted(numbers)
    min_diff = float('inf')
    best_pair = (nums_sorted[0], nums_sorted[1])
    for i in range(len(nums_sorted) - 1):
        a = nums_sorted[i]
        b = nums_sorted[i + 1]
        diff = b - a
        if diff < min_diff:
            min_diff = diff
            best_pair = (a, b)
    return best_pair