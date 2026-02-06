from typing import List

def separate_paren_groups(paren_string: str) -> list:
    s = ''.join(paren_string.split())
    groups = []
    curr = []
    balance = 0
    for ch in s:
        if ch not in '()':
            continue
        curr.append(ch)
        if ch == '(':
            balance += 1
        else:
            balance -= 1
        if balance == 0 and curr:
            groups.append(''.join(curr))
            curr = []
    return groups