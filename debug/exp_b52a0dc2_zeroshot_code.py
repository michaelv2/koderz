def split_words(txt):
    if any(ch.isspace() for ch in txt):
        return txt.split()
    if ',' in txt:
        return txt.split(',')
    a = ord('a')
    count = 0
    for ch in txt:
        o = ord(ch)
        if a <= o <= a + 25 and ((o - a) % 2) == 1:
            count += 1
    return count