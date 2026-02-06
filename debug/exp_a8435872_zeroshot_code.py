def get_odd_collatz(n):
    if not isinstance(n, int) or n <= 0:
        raise ValueError("n must be a positive integer")
    odds = set()
    current = n
    while True:
        if current % 2 == 1:
            odds.add(current)
        if current == 1:
            break
        if current % 2 == 0:
            current //= 2
        else:
            current = 3 * current + 1
    return sorted(odds)