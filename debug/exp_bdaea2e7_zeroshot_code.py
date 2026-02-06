def starts_one_ends(n):
    if n == 1:
        return 1  # Only '1' is the single-digit number that starts and ends with 1
    return 2 * (10 ** (n - 1)) - (10 ** (n - 2))