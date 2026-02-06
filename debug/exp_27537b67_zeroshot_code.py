from typing import List

def mean_absolute_deviation(numbers: List[float]) -> float:
    if not numbers:
        return 0.0  # Return 0 for an empty list to avoid division by zero
    
    # Step 1: Calculate the mean of the numbers
    mean = sum(numbers) / len(numbers)
    
    # Step 2: Calculate the absolute deviations from the mean
    absolute_deviations = [abs(x - mean) for x in numbers]
    
    # Step 3: Calculate the mean of these absolute deviations
    mad = sum(absolute_deviations) / len(absolute_deviations)
    
    return mad