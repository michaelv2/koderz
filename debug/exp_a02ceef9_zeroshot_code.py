def words_string(s):
    """
    You will be given a string of words separated by commas or spaces. Your task is
    to split the string into words and return an array of the words.
    """
    # Replace commas with spaces and split by whitespace
    # This handles both comma and space separators
    words = s.replace(",", " ").split()
    return words