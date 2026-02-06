from typing import List

def remove_duplicates(numbers: List[int]) -> List[int]:
    from collections import Counter
    counts = Counter(numbers)
    return [x for x in numbers if counts[x] == 1]