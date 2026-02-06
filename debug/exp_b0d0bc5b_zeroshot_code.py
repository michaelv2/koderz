from typing import List

def remove_duplicates(numbers: List[int]) -> List[int]:
    count = {}
    for number in numbers:
        if number in count:
            count[number] += 1
        else:
            count[number] = 1
    return [number for number in numbers if count[number] == 1]