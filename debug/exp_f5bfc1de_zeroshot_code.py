def get_max_triples(n):
    """
    You are given a positive integer n. You have to create an integer array a of length n.
    For each i (1 ≤ i ≤ n), the value of a[i] = i * i - i + 1.
    Return the number of triples (a[i], a[j], a[k]) of a where i < j < k, 
    and a[i] + a[j] + a[k] is a multiple of 3.
    """
    c0 = (n + 1) // 3  # i % 3 == 2 -> value 0 mod 3
    c1 = n - c0        # i % 3 == 0 or 1 -> value 1 mod 3

    def comb3(x):
        if x < 3:
            return 0
        return x * (x - 1) * (x - 2) // 6

    return comb3(c0) + comb3(c1)