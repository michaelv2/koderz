from typing import List, Tuple

def find_closest_elements(numbers: List[float]) -> Tuple[float, float]:
    numbers.sort()  # Sort the list in ascending order
    min_diff = float('inf')  # Initialize minimum difference as infinity
    closest_pair = (None, None)  # Initialize closest pair as none
    
    for i in range(1, len(numbers)):
        diff = numbers[i] - numbers[i-1]  # Calculate the difference with previous number
        
        if diff < min_diff:  # If this difference is less than current minimum difference
            min_diff = diff  # Update the minimum difference
            closest_pair = (numbers[i-1], numbers[i])  # And update the closest pair
            
    return closest_pair