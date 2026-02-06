def generate_integers(a, b):
    # Swap the numbers if a is greater than b
    if a > b:
        a, b = b, a
    
    result = []
    for num in range(a, b + 1):
        if num % 2 == 0:
            result.append(num)
            
    return result