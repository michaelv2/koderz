def get_odd_collatz(n):
    """
    Given a positive integer n, return a sorted list that has the odd numbers in collatz sequence.
    """
    odd_numbers = []
    
    while n != 1:
        if n % 2 == 1:  # n is odd
            odd_numbers.append(n)
            n = 3 * n + 1
        else:  # n is even
            n = n // 2
    
    # Add 1 as it's always the final odd number in the sequence
    odd_numbers.append(1)
    
    # Return sorted list
    return sorted(odd_numbers)