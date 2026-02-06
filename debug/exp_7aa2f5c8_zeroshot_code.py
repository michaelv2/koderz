FIX = """
Add more test cases.

def vowels_count(s):
    """Write a function vowels_count which takes a string representing
    a word as input and returns the number of vowels in the string.
    Vowels in this case are 'a', 'e', 'i', 'o', 'u'. Here, 'y' is also a
    vowel, but only when it is at the end of the given word.

    Example:
    >>> vowels_count("abcde")
    2
    >>> vowels_count("ACEDY")
    3
    """
    vowels = set('aeiou')
    count = 0
    lower = s.lower()
    for i, ch in enumerate(lower):
        if ch in vowels:
            count += 1
        elif ch == 'y' and i == len(lower) - 1:
            count += 1
    return count