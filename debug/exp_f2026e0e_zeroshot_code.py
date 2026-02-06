def count_distinct_characters(string: str) -> int:
    """ Given a string, find out how many distinct characters (regardless of case) does it consist of """
    # Convert the string to lowercase to ignore case sensitivity
    lower_string = string.lower()
    
    # Use a set to store unique characters
    unique_chars = set(lower_string)
    
    # Return the number of distinct characters
    return len(unique_chars)