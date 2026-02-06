def anti_shuffle(s):
    """
    Write a function that takes a string and returns an ordered version of it.
    Ordered version of string, is a string where all words (separated by space)
    are replaced by a new word where all the characters arranged in
    ascending order based on ascii value.
    Note: You should keep the order of words and blank spaces in the sentence.
    """
    # Split on literal space to preserve multiple spaces as empty tokens
    parts = s.split(' ')
    # Sort characters of each non-empty token by ASCII (default of sorted)
    parts = [''.join(sorted(p)) if p != '' else '' for p in parts]
    # Rejoin with spaces to restore original spacing
    return ' '.join(parts)