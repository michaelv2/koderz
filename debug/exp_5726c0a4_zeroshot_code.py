def split_words(txt):
    if any(c.isspace() for c in txt):
        return txt.split()
    if ',' in txt:
        return txt.split(',')
    count = 0
    for c in txt:
        if 'a' <= c <= 'z' and ((ord(c) - ord('a')) % 2 == 1):
            count += 1
    return count