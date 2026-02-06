from typing import List

def separate_paren_groups(paren_string: str) -> List[str]:
    res = []
    cur = []
    balance = 0
    for ch in paren_string:
        if ch == ' ':
            continue
        if ch == '(':
            balance += 1
            cur.append('(')
        elif ch == ')':
            balance -= 1
            cur.append(')')
        else:
            continue
        if balance == 0 and cur:
            res.append(''.join(cur))
            cur = []
    return res