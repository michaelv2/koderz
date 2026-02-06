from typing import List, Tuple

def find_closest_elements(numbers: List[float]) -> Tuple[float, float]:
    if len(numbers) < 2:
        raise ValueError("numbers must contain at least two elements")
    nums = sorted(numbers)
    best_pair = (nums[0], nums[1])
    best_diff = nums[1] - nums[0]
    for i in range(2, len(nums)):
        diff = nums[i] - nums[i - 1]
        if diff < best_diff:
            best_diff = diff
            best_pair = (nums[i - 1], nums[i])
    return best_pair