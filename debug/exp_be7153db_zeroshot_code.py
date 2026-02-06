def tri(n):
    if n < 0:
        return []
    res = [0] * (n + 1)
    for i in range(n + 1):
        if i == 0:
            res[i] = 1
        elif i == 1:
            res[i] = 3
        elif i % 2 == 0:
            res[i] = 1 + i // 2
        else:
            # i is odd and >= 3
            res[i] = res[i - 1] + res[i - 2] + (1 + (i + 1) // 2)
    return res