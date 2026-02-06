def is_simple_power(x, n):
    if x == 1:
        return n != 0
    if n == 0:
        return x == 0
    if n == 1:
        return x == 1
    if n == -1:
        return x in (1, -1)
    val = 1
    while abs(val) <= abs(x):
        if val == x:
            return True
        val *= n
    return False