from typing import List, Tuple
import functools
import operator

def sum_product(numbers: List[int]) -> Tuple[int, int]:
    if not numbers:  # If the list is empty
        return (0, 1)
    else:
        total_sum = sum(numbers)
        product = functools.reduce(operator.mul, numbers, 1)
        return (total_sum, product)