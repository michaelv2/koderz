import re

def is_bored(S):
    if not isinstance(S, str):
        S = str(S)
    count = 0
    parts = re.split(r'[.!?]', S)
    for part in parts:
        words = re.findall(r"[A-Za-z]+", part)
        if words and words[0] == 'I':
            count += 1
    return count