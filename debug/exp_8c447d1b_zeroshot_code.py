def get_max_triples(n):
    if n < 3:
        return 0
    n0 = n // 3 + (1 if n % 3 >= 2 else 0)  # count of i with i % 3 == 2
    n1 = n - n0  # count of i with i % 3 in {0, 1}
    res = 0
    if n0 >= 3:
        res += n0 * (n0 - 1) * (n0 - 2) // 6
    if n1 >= 3:
        res += n1 * (n1 - 1) * (n1 - 2) // 6
    return res