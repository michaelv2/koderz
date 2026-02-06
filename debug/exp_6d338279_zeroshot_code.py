from typing import List

def remove_duplicates(numbers: List[int]) -> List[int]:
    num_count = {}
    for num in numbers:
        if num in num_count:
            num_count[num] += 1
        else:
            num_count[num] = 1
    return [num for num in numbers if num_count[num] == 1]