from typing import List

def sort_numbers(numbers: str) -> str:
    # Create mapping from words to numbers
    word_to_num = {
        'zero': 0,
        'one': 1,
        'two': 2,
        'three': 3,
        'four': 4,
        'five': 5,
        'six': 6,
        'seven': 7,
        'eight': 8,
        'nine': 9
    }
    
    # Split the input string into words
    word_list = numbers.split()
    
    # Sort words based on their numeric values
    sorted_words = sorted(word_list, key=lambda word: word_to_num[word])
    
    # Join back into a space-delimited string
    return ' '.join(sorted_words)