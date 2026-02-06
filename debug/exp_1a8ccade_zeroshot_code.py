def prod_signs(arr):
    # If the array is empty, return None
    if not arr:
        return None
    
    product = 1
    sum_magnitudes = 0
    
    for num in arr:
        # Calculate the sign of each number and multiply it with the current product
        product *= -1 if num < 0 else 1
        
        # Add the magnitude of each number to the sum of magnitudes
        sum_magnitudes += abs(num)
    
    return product * sum_magnitudes