def is_simple_power(x, n):
    if n == 0:
        # 0^k = 0 for k >= 1; 0^0 is undefined
        return x == 0
    if n == 1:
        # 1^k = 1 for any k >= 0
        return x == 1
    if x <= 0:
        return False
    while x % n == 0:
        x //= n
    return x == 1