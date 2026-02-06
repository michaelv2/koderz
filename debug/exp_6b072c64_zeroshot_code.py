def how_many_times(string: str, substring: str) -> int:
    """Count overlapping occurrences of substring in string."""
    if not substring:
        return 0
    sub_len = len(substring)
    limit = len(string) - sub_len
    if limit < 0:
        return 0
    count = 0
    for i in range(limit + 1):
        if string[i:i + sub_len] == substring:
            count += 1
    return count