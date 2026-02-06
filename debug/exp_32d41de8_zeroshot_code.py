from typing import List

def remove_duplicates(numbers: List[int]) -> List[int]:
    """ From a list of integers, remove all elements that occur more than once.
    Keep order of elements left the same as in the input.
    >>> remove_duplicates([1, 2, 3, 2, 4])
    [1, 3, 4]
    """
    # Count frequency of each number
    freq = {}
    for num in numbers:
        freq[num] = freq.get(num, 0) + 1
    
    # Keep only numbers that appear exactly once, maintaining order
    result = []
    for num in numbers:
        if freq[num] == 1:
            result.append(num)
    
    return result