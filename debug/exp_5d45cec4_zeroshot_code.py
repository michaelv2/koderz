def triples_sum_to_zero(l: list):
    if len(l) < 3:
        return False
    
    # Sort the list to enable two-pointer technique
    sorted_l = sorted(l)
    
    # For each element, check if there are two other elements that sum to its negative
    for i in range(len(sorted_l) - 2):
        # Use two pointers to find if any two elements sum to -sorted_l[i]
        left = i + 1
        right = len(sorted_l) - 1
        
        while left < right:
            current_sum = sorted_l[i] + sorted_l[left] + sorted_l[right]
            
            if current_sum == 0:
                return True
            elif current_sum < 0:
                left += 1
            else:
                right -= 1
    
    return False