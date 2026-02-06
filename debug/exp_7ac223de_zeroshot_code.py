def tribonacci_sequence(n):
    # Initialize the sequence with the first three numbers
    seq = [1, 3, 2]
    
    for i in range(3, n+1):
        if i % 2 == 0:
            seq.append(int(1 + i / 2))
        else:
            seq.append(seq[i-1] + seq[i-2] + seq[i])
    
    return seq[:n+1]