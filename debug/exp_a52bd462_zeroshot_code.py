def count_distinct_characters(string: str) -> int:
    """ Given a string, find out how many distinct characters (regardless of case) does it consist of """
    lower_string = string.lower()
    unique_chars = set(lower_string)
    return len(unique_chars)