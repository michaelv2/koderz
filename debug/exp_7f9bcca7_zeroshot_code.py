def anti_shuffle(s):
    return ' '.join(''.join(sorted(tok)) for tok in s.split(' '))