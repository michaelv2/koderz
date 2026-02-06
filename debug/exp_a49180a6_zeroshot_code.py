def starts_one_ends(n):
    # Total number of n-digit numbers is 10^n - 10^(n-1)
    total = 10 ** n - 10 ** (n - 1)

    # If the number has only one digit, there are no numbers that neither start nor end with 1
    if n == 1:
        return total

    # Numbers that neither start nor end with 1 is 10^(n-1) - (n-2)
    # We subtract this from the total count
    return total - (10 ** (n - 1) - (n - 2))