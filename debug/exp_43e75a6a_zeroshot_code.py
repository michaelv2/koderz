from typing import List

def sort_numbers(numbers: str) -> str:
    nums = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
    numbers = numbers.split()
    sorted_numbers = sorted(numbers, key=lambda x: nums.index(x))
    return ' '.join(sorted_numbers)