def will_it_fly(q, w):
    # Check if the list is palindromic (balanced)
    is_balanced = q == q[::-1]
    
    # Check if the sum of elements is within the weight limit
    weight_ok = sum(q) <= w
    
    # Return True only if both conditions are met
    return is_balanced and weight_ok