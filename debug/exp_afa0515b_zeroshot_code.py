def remove_vowels(text):
    """
    remove_vowels is a function that takes string and returns string without vowels.
    """
    return ''.join(ch for ch in text if ch.lower() not in 'aeiou')