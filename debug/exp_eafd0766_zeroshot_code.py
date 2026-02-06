def count_nums(arr):
    count = 0
    for n in arr:
        if n == 0:
            s = 0
        else:
            s = 0
            sign = -1 if n < 0 else 1
            for i, ch in enumerate(str(abs(n))):
                d = int(ch)
                if i == 0:
                    d *= sign
                s += d
        if s > 0:
            count += 1
    return count