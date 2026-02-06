from typing import List

def sort_numbers(numbers: str) -> str:
    # Mapping of number words to their corresponding integer values
    num_map = {
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
    
    # Inverse mapping from integer values to number words
    reverse_num_map = {v: k for k, v in num_map.items()}
    
    # Split the input string into a list of number words
    num_words = numbers.split()
    
    # Convert number words to integers
    num_values = [num_map[word] for word in num_words]
    
    # Sort the list of integers
    sorted_num_values = sorted(num_values)
    
    # Convert sorted integers back to number words
    sorted_num_words = [reverse_num_map[value] for value in sorted_num_values]
    
    # Join the sorted number words into a single string
    return ' '.join(sorted_num_words)