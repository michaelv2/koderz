def special_factorial(n):
    """The Brazilian factorial is defined as the product of k! for k=1..n."""
    if n <= 0:
        # According to the problem n > 0, but handle non-positive gracefully
        return 1
    product = 1
    fact = 1
    for k in range(1, n + 1):
        fact *= k
        product *= fact
    return product