from typing import List, Tuple

def sum_product(numbers: List[int]) -> Tuple[int, int]:
    total = sum(numbers)
    prod = 1
    for n in numbers:
        prod *= n
    return total, prod