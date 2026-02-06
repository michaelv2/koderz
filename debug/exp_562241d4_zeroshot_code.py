def get_max_triples(n):
    c0 = n // 3 + (1 if n % 3 >= 2 else 0)
    c1 = n - c0
    def choose3(x):
        return x * (x - 1) * (x - 2) // 6 if x >= 3 else 0
    return choose3(c0) + choose3(c1)