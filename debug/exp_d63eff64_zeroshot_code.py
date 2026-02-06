def how_many_times(string: str, substring: str) -> int:
    """Find how many times a given substring can be found in the original string.
    Count overlapping occurrences. Returns 0 if substring is empty.
    """
    if not substring:
        return 0
    count = 0
    k = len(substring)
    n = len(string)
    for i in range(n - k + 1):
        if string[i:i + k] == substring:
            count += 1
    return count