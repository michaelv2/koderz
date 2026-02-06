from typing import List

def intersperse(numbers: List[int], delimeter: int) -> List[int]:
    result = []
    for num in numbers:
        result.append(num)
        if num != numbers[-1]:  # Check if it's not the last element
            result.append(delimeter)
    return result