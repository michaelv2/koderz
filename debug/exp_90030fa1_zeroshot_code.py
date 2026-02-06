from typing import List

def sort_numbers(numbers: str) -> str:
    """ Input is a space-delimited string of numberals from 'zero' to 'nine'.
    Return the string with numbers sorted from smallest to largest.
    """
    word_to_val = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9
    }
    if not numbers:
        return ''
    tokens = [t for t in numbers.split() if t != '']
    # sort using mapping; assume inputs are valid words
    tokens.sort(key=lambda w: word_to_val.get(w, 0))
    return ' '.join(tokens)