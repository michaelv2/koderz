def fizz_buzz(n: int):
    """Return the number of times the digit 7 appears in integers less than n which are divisible by 11 or 13."""
    count = 0
    for k in range(n):
        if k % 11 == 0 or k % 13 == 0:
            count += str(k).count('7')
    return count