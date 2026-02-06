def fizz_buzz(n: int):
    """Return the number of times the digit 7 appears in integers less than n which are divisible by 11 or 13.
    >>> fizz_buzz(50)
    0
    >>> fizz_buzz(78)
    2
    >>> fizz_buzz(79)
    3
    """
    if n <= 0:
        return 0

    numbers = set()
    for x in range(0, n, 11):
        numbers.add(x)
    for x in range(0, n, 13):
        numbers.add(x)

    count = 0
    for m in numbers:
        count += str(m).count('7')
    return count