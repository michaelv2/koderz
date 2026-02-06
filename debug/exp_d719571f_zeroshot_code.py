def get_odd_collatz(n):
    odd_numbers = []
    while n != 1:
        if n % 2 != 0:
            odd_numbers.append(n)
        if n % 2 == 0:
            n //= 2
        else:
            n = 3 * n + 1
    odd_numbers.append(1)  # Add the final number 1 to the list
    return sorted(odd_numbers)