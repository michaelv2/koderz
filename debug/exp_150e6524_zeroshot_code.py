def count_upper(s):
    """
    Given a string s, count the number of uppercase vowels in even indices.
    """
    vowels = set("AEIOU")
    return sum(1 for i, ch in enumerate(s) if i % 2 == 0 and ch in vowels)