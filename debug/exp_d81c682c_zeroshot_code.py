def sort_even(l):
    even_indices = [x for i, x in enumerate(l) if i % 2 == 0]
    even_indices.sort()
    
    result = []
    for i in range(len(l)):
        if i % 2 == 0:
            result.append(even_indices.pop(0))
        else:
            result.append(l[i])
            
    return result