from typing import List, Tuple

def find_closest_elements(numbers: List[float]) -> Tuple[float, float]:
    sorted_numbers = sorted(numbers)
    min_distance = float('inf')
    closest_pair = (0, 0)
    
    for i in range(len(sorted_numbers) - 1):
        distance = sorted_numbers[i + 1] - sorted_numbers[i]
        if distance < min_distance:
            min_distance = distance
            closest_pair = (sorted_numbers[i], sorted_numbers[i + 1])
    
    return closest_pair