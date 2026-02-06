from typing import List

def sort_numbers(numbers: str) -> str:
    nums = ['zero','one','two','three','four','five','six','seven','eight','nine']
    parts = numbers.split()
    return ' '.join(sorted(parts, key=lambda w: nums.index(w))) if parts else ''