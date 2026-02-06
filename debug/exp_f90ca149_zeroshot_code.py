def is_simple_power(x, n):
    if n == 1:
        return x == 1
    if n == 0:
        return x == 0
    if x == 1:
        return True
    if n == -1:
        return x in (1, -1)
    if n == 0:
        return False
    if x == 0:
        return n != 0 and False
    while n != 0 and x % n == 0:
        x //= n
    return x == 1