def count_distinct_characters(string: str) -> int:
    """ Given a string, find out how many distinct characters (regardless of case) does it consist of """
    if string is None:
        return 0
    return len(set(string.lower()))