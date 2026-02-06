def how_many_times(string: str, substring: str) -> int:
    count = 0
    start = 0
    while start <= len(string) - len(substring):
        if string[start:start + len(substring)] == substring:
            count += 1
        start += 1
    return count