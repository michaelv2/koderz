def tri(n):
    if n < 0:
        return []
    
    # Initialize the sequence with base cases
    sequence = [0] * (n + 1)
    sequence[1] = 3
    
    for i in range(2, n + 1):
        if i % 2 == 0:
            sequence[i] = 1 + i // 2
        else:
            # Ensure we have the next value calculated before using it
            if i < n:
                sequence[i + 1] = 1 + (i + 1) // 2
            sequence[i] = sequence[i - 1] + sequence[i - 2] + sequence[i + 1]
    
    return sequence[:n + 1]