def is_simple_power(x, n):
    if x == 1 or n == 1:
        return True
    else:
        i = n
        while i < x:
            i *= n
        return i == x