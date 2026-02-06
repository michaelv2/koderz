def count_nums(arr):
    c = 0
    for n in arr:
        if n == 0:
            s = 0
        elif n > 0:
            s = sum(int(d) for d in str(n))
        else:
            a = str(-n)
            first = -int(a[0])
            rest = sum(int(d) for d in a[1:]) if len(a) > 1 else 0
            s = first + rest
        if s > 0:
            c += 1
    return c