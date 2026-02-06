def get_max_triples(n):
    if n < 3:
        return 0
    n0 = (n + 1) // 3  # count of i with i % 3 == 2
    n1 = n - n0        # count of i with i % 3 in {0, 1}
    
    def comb3(x):
        if x < 3:
            return 0
        return x * (x - 1) * (x - 2) // 6
    
    return comb3(n0) + comb3(n1)