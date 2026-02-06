from typing import List

def intersperse(numbers: List[int], delimeter: int) -> List[int]:
    """ Insert a number 'delimeter' between every two consecutive elements of input list `numbers' """
    if not numbers:
        return []
    result: List[int] = []
    last_index = len(numbers) - 1
    for i, num in enumerate(numbers):
        result.append(num)
        if i != last_index:
            result.append(delimeter)
    return result