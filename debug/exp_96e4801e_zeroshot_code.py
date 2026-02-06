from typing import List, Tuple

from typing import List

def rolling_max(numbers: List[int]) -> List[int]:
    if not numbers:
        return []

    rolling_maximums = [numbers[0]]

    for num in numbers[1:]:
        if num > rolling_maximums[-1]:
            rolling_maximums.append(num)
        else:
            rolling_maximums.append(rolling_maximums[-1])

    return rolling_maximums