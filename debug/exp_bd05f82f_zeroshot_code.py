def get_max_triples(n):
    from math import comb
    
    # Count elements with remainder 0 and 1 when divided by 3
    count_0 = 0  # elements where a[i] ≡ 0 (mod 3)
    count_1 = 0  # elements where a[i] ≡ 1 (mod 3)
    
    for i in range(1, n + 1):
        val = i * i - i + 1
        if val % 3 == 0:
            count_0 += 1
        else:
            count_1 += 1
    
    # Number of triples where all have remainder 0: C(count_0, 3)
    # Number of triples where all have remainder 1: C(count_1, 3)
    result = comb(count_0, 3) + comb(count_1, 3)
    
    return result