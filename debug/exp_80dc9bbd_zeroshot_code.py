def triples_sum_to_zero(l: list):
    n = len(l)
    for i in range(n):
        seen = set()
        target = -l[i]
        for j in range(i + 1, n):
            if target - l[j] in seen:
                return True
            seen.add(l[j])
    return False