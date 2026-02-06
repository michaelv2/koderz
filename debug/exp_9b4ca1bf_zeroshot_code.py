def get_odd_collatz(n):
    if n <= 0:
        return []
    odds = set()
    x = int(n)
    while True:
        if x % 2 == 1:
            odds.add(x)
        if x == 1:
            break
        if x % 2 == 0:
            x //= 2
        else:
            x = 3 * x + 1
    return sorted(odds)