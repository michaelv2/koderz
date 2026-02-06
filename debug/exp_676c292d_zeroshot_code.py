def split_words(txt):
    """
    Split input as follows:
    - If any whitespace characters are present, split on whitespace and return the list.
    - Else if a comma is present, split on commas and return the list.
    - Else return the count of lowercase letters 'a'..'z' whose index (a=0, b=1, ...) is odd.
    """
    if any(ch.isspace() for ch in txt):
        return txt.split()
    if ',' in txt:
        return txt.split(',')
    count = 0
    base = ord('a')
    for ch in txt:
        if 'a' <= ch <= 'z':
            if (ord(ch) - base) % 2 == 1:
                count += 1
    return count