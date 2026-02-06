def sort_third(l):
    # Create a list of elements at indices divisible by three
    divisible_by_three = sorted([elem for i, elem in enumerate(l) if i % 3 == 0])
    
    # Replace the elements at indices divisible by three with the sorted ones
    for i in range(len(l)):
        if i % 3 == 0:
            l[i] = divisible_by_three.pop(0)
            
    return l