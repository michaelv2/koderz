def split_words(txt):
    if any(ch.isspace() for ch in txt):
        return txt.split()
    if ',' in txt:
        parts = txt.split(',')
        return [p for p in parts if p != ""]
    count = 0
    base = ord('a')
    for ch in txt:
        o = ord(ch)
        if 97 <= o <= 122:
            if (o - base) % 2 == 1:
                count += 1
    return count