from typing import List

def sort_numbers(numbers: str) -> str:
    order = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9
    }
    if not numbers:
        return ""
    tokens = numbers.split()
    tokens.sort(key=lambda w: order[w])
    return " ".join(tokens)