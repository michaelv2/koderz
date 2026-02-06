def how_many_times(string: str, substring: str) -> int:
    """ Find how many times a given substring can be found in the original string. Count overlaping cases. """
    if not substring:
        return 0
    count = 0
    sub_len = len(substring)
    max_start = len(string) - sub_len
    for i in range(max_start + 1):
        if string[i:i+sub_len] == substring:
            count += 1
    return count