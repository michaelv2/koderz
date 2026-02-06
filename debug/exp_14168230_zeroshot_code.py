def sort_third(l: list):
    # Collect elements at indices divisible by 3
    divisible_by_three = [l[i] for i in range(len(l)) if i % 3 == 0]
    
    # Sort the collected elements
    sorted_divisible_by_three = sorted(divisible_by_three)
    
    # Create a new list with sorted elements at indices divisible by 3
    result = l[:]
    index = 0
    for i in range(len(l)):
        if i % 3 == 0:
            result[i] = sorted_divisible_by_three[index]
            index += 1
    
    return result