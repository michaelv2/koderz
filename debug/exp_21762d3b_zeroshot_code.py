from typing import List

def sort_numbers(numbers: str) -> str:
    num_map = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9
    }
    reverse_num_map = {v: k for k, v in num_map.items()}
    
    # Convert words to numbers
    num_list = [num_map[word] for word in numbers.split()]
    
    # Sort the numbers
    sorted_num_list = sorted(num_list)
    
    # Convert numbers back to words
    sorted_words = [reverse_num_map[num] for num in sorted_num_list]
    
    # Join and return the result
    return ' '.join(sorted_words)