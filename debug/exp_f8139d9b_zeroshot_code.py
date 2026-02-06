def starts_one_ends(n):
    if n == 1:
        return 1
    else:
        return 10**n - 10**(n-2)