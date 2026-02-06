import re

def is_bored(S):
    parts = re.split(r'[.?!]', S)
    count = 0
    for p in parts:
        p = p.strip()
        if not p:
            continue
        words = p.split()
        if words and words[0] == 'I':
            count += 1
    return count