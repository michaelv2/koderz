from typing import List

def has_close_elements(numbers: List[float], threshold: float) -> bool:
    if threshold <= 0:
        return False
    nums = sorted(numbers)
    for i in range(1, len(nums)):
        if nums[i] - nums[i - 1] < threshold:
            return True
    return False