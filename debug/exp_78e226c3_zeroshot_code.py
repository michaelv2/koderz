def tri(n):
    """Return list of tribonacci values from index 0 to n inclusive."""
    res = []
    for i in range(n + 1):
        if i == 1:
            val = 3
        elif i % 2 == 0:
            val = 1 + i // 2
        else:
            # i is odd and i != 1; tri(i+1) is even so use direct formula
            next_even = 1 + (i + 1) // 2
            val = res[i - 1] + res[i - 2] + next_even
        res.append(val)
    return res