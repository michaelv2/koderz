def split_words(txt):
    if any(ch.isspace() for ch in txt):
        return txt.split()
    if ',' in txt:
        return txt.split(',')
    return sum(1 for c in txt if 'a' <= c <= 'z' and ((ord(c) - ord('a')) % 2 == 1))