def tri(n):
    if n < 0:
        return []
    res = []
    for k in range(n + 1):
        if k == 0:
            res.append(1)
        elif k == 1:
            res.append(3)
        elif k == 2:
            res.append(2)
        elif k % 2 == 0:
            res.append(1 + k // 2)
        else:
            # k is odd and >= 3
            res.append(res[k - 1] + res[k - 2] + (1 + (k + 1) // 2))
    return res