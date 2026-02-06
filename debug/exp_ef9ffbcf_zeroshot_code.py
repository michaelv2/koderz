def tri(n):
    if n < 0:
        return []
    res = [0] * (n + 1)
    res[0] = 1
    if n >= 1:
        res[1] = 3
    for i in range(2, n + 1):
        if i % 2 == 0:
            res[i] = 1 + i // 2
        else:
            res[i] = res[i - 1] + res[i - 2] + (1 + (i + 1) // 2)
    return res