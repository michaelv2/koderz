def how_many_times(string: str, substring: str) -> int:
    """ Find how many times a given substring can be found in the original string. Count overlapping cases. """
    if not substring:
        return 0
    n, m = len(string), len(substring)
    if m > n:
        return 0
    count = 0
    for i in range(n - m + 1):
        if string[i:i + m] == substring:
            count += 1
    return count