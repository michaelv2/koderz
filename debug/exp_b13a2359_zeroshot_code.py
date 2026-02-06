from typing import List, Tuple

from typing import List


def rolling_max(numbers: List[int]) -> List[int]:
    """ From a given list of integers, generate a list of rolling maximum element found until given moment in the sequence.
    >>> rolling_max([1, 2, 3, 2, 3, 4, 2])
    [1, 2, 3, 3, 3, 4, 4]
    """
    if not numbers:
        return []
    
    result = []
    current_max = float('-inf')
    
    for number in numbers:
        if number > current_max:
            current_max = number
        result.append(current_max)
    
    return result