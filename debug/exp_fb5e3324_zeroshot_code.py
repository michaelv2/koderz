def get_odd_collatz(n):
    collatz_sequence = []
    while n != 1:
        if n % 2 == 0:
            n = n // 2
        else:
            collatz_sequence.append(n)
            n = 3 * n + 1
    collatz_sequence.append(1)  # Add the final term of the sequence, which is 1
    return sorted(collatz_sequence)