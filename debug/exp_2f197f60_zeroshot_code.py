def prod_signs(arr):
    if not arr:
        return None
    
    # Sum of magnitudes (absolute values)
    magnitude_sum = sum(abs(x) for x in arr)
    
    # Product of signs
    sign_product = 1
    for num in arr:
        if num == 0:
            sign_product = 0
            break
        elif num < 0:
            sign_product *= -1
    
    return magnitude_sum * sign_product