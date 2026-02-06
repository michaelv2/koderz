from typing import List

def intersperse(numbers: List[int], delimeter: int) -> List[int]:
    if not numbers:
        return []
    result = []
    last_index = len(numbers) - 1
    for i, n in enumerate(numbers):
        result.append(n)
        if i != last_index:
            result.append(delimeter)
    return result