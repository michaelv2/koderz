def count_upper(s):
    """
    Given a string s, count the number of uppercase vowels in even indices.
    """
    vowels = set("AEIOU")
    count = 0
    for i in range(0, len(s), 2):
        if s[i] in vowels:
            count += 1
    return count