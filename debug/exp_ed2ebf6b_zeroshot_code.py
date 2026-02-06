from typing import List

def has_close_elements(numbers, threshold) -> bool:
    """Return True if any two elements are closer to each other than the given threshold."""
    if threshold <= 0 or len(numbers) < 2:
        return False
    nums = sorted(numbers)
    for i in range(1, len(nums)):
        if nums[i] - nums[i - 1] < threshold:
            return True
    return False