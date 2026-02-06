from typing import List

def sort_numbers(numbers: str) -> str:
    """ Input is a space-delimited string of numberals from 'zero' to 'nine'.
    Valid choices are 'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight' and 'nine'.
    Return the string with numbers sorted from smallest to largest
    >>> sort_numbers('three one five')
    'one three five'
    """
    # Mapping from word to number
    word_to_num = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9
    }
    
    # Mapping from number to word
    num_to_word = {v: k for k, v in word_to_num.items()}
    
    # Parse input and convert to numbers
    word_list = numbers.split()
    num_list = [word_to_num[word] for word in word_list]
    
    # Sort the numbers
    num_list.sort()
    
    # Convert back to words and join
    result = ' '.join(num_to_word[num] for num in num_list)
    
    return result