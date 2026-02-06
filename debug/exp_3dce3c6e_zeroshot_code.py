from typing import List, Tuple

def rolling_max(numbers):
    max_list = []
    current_max = float('-inf')
    for num in numbers:
        if num > current_max:
            current_max = num
        max_list.append(current_max)
    return max_list