def sort_even(l: list):
    even_indices = [i for i in range(len(l)) if i % 2 == 0]
    even_values = sorted([l[i] for i in even_indices])
    
    l_prime = l[:]
    for idx, value in zip(even_indices, even_values):
        l_prime[idx] = value
    
    return l_prime