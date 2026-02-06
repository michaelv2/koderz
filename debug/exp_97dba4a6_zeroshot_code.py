from typing import List

def remove_duplicates(numbers: List[int]) -> List[int]:
    """
    From a list of integers, remove all elements that occur more than once.
    Keep order of elements left the same as in the input.
    """
    counts = {}
    for x in numbers:
        counts[x] = counts.get(x, 0) + 1
    return [x for x in numbers if counts[x] == 1]