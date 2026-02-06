from typing import List

def mean_absolute_deviation(numbers: List[float]) -> float:
    if not numbers:
        return 0.0
    
    # Step 1: Calculate the mean of the numbers
    mean = sum(numbers) / len(numbers)
    
    # Step 2: Calculate the absolute differences from the mean
    absolute_differences = [abs(x - mean) for x in numbers]
    
    # Step 3: Calculate the mean of these absolute differences
    mad = sum(absolute_differences) / len(numbers)
    
    return mad